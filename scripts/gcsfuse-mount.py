#!/usr/bin/env python3
"""
GCS FUSE Mount Script
Mounts a GCS bucket using gcsfuse and keeps the sidecar container running.
"""

import os
import subprocess
import time
import signal
import sys
import logging
from pathlib import Path
from typing import Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GCSFuseManager:
    def __init__(self) -> None:
        self.bucket_name = os.getenv('GCS_BUCKET_NAME', 'infinigram_v4_pileval_llama')
        self.mount_point = os.getenv('MOUNT_POINT', '/mnt/infinigram-array/v4_pileval_llama')
        self.shared_mount_point = os.getenv('SHARED_MOUNT_POINT', '/mnt/infinigram-array-shared')
        self.mount_process: Optional[subprocess.Popen[Any]] = None
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame: object) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.mount_process and self.mount_process.poll() is None:
            logger.info("Terminating mount process...")
            self.mount_process.terminate()
    
    def install_gcsfuse(self) -> None:
        """Install gcsfuse and dependencies."""
        logger.info("Installing gcsfuse dependencies...")
        
        try:
            # Update package list
            subprocess.run(['apt-get', 'update'], check=True)
            
            # Install required packages
            subprocess.run(['apt-get', 'install', '-y', 'lsb-release', 'curl'], check=True)
            
            # Get distribution codename
            result = subprocess.run(['lsb_release', '-c', '-s'], 
                                  capture_output=True, text=True, check=True)
            codename = result.stdout.strip()
            
            # Add gcsfuse repository
            repo_line = f"deb http://packages.cloud.google.com/apt gcsfuse-{codename} main"
            with open('/etc/apt/sources.list.d/gcsfuse.list', 'w') as f:
                f.write(repo_line + '\n')
            
            # Add GPG key
            subprocess.run(['curl', 'https://packages.cloud.google.com/apt/doc/apt-key.gpg'], 
                         stdout=subprocess.PIPE, check=True)
            curl_process = subprocess.Popen(
                ['curl', 'https://packages.cloud.google.com/apt/doc/apt-key.gpg'],
                stdout=subprocess.PIPE
            )
            subprocess.run(['apt-key', 'add', '-'], 
                         stdin=curl_process.stdout, check=True)
            curl_process.wait()
            
            # Update and install gcsfuse
            subprocess.run(['apt-get', 'update'], check=True)
            subprocess.run(['apt-get', 'install', '-y', 'gcsfuse'], check=True)
            
            logger.info("gcsfuse installation completed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install gcsfuse: {e}")
            sys.exit(1)
    
    def create_mount_point(self) -> None:
        """Create the mount point directory."""
        try:
            Path(self.mount_point).mkdir(parents=True, exist_ok=True)
            Path(self.shared_mount_point).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created mount points: {self.mount_point}, {self.shared_mount_point}")
        except Exception as e:
            logger.error(f"Failed to create mount point: {e}")
            sys.exit(1)
    
    def mount_bucket(self) -> None:
        """Mount the GCS bucket using gcsfuse."""
        logger.info(f"Mounting bucket {self.bucket_name} to {self.mount_point}...")
        
        try:
            # Start gcsfuse in the background
            self.mount_process = subprocess.Popen([
                'gcsfuse',
                '--implicit-dirs',
                '--foreground',
                self.bucket_name,
                self.mount_point
            ])
            
            logger.info(f"Mount process started with PID: {self.mount_process.pid}")
            
            # Wait for mount to be ready
            time.sleep(10)
            
            # Check if mount was successful
            if self.mount_process.poll() is not None:
                logger.error("Mount process exited unexpectedly")
                sys.exit(1)
            
            self._verify_mount()
            
        except Exception as e:
            logger.error(f"Failed to mount bucket: {e}")
            sys.exit(1)
    
    def _verify_mount(self) -> None:
        """Verify that the mount is working."""
        try:
            files = list(Path(self.mount_point).iterdir())
            logger.info(f"Mount successful. Found {len(files)} items in {self.mount_point}")
            
            # Log first few items
            for i, item in enumerate(files[:5]):
                logger.info(f"  {item.name}")
                
        except Exception as e:
            logger.warning(f"Could not verify mount contents: {e}")
    
    def copy_files_to_shared_volume(self) -> None:
        """Copy files from mount to shared volume."""
        logger.info("Copying files to shared volume...")
        
        try:
            # Use cp command for efficient copying
            subprocess.run([
                'cp', '-r', f'{self.mount_point}/*', self.shared_mount_point
            ], shell=True, check=False)  # Don't fail if no files to copy
            
            # Verify copy
            shared_files = list(Path(self.shared_mount_point).iterdir())
            logger.info(f"Copied files to shared volume. Found {len(shared_files)} items")
            
        except Exception as e:
            logger.warning(f"Error copying files to shared volume: {e}")
    
    def monitor_mount(self) -> None:
        """Monitor the mount process and keep the container alive."""
        logger.info("Starting mount monitoring...")
        
        sync_interval = 30  # seconds
        last_sync = time.time()
        
        while self.running:
            try:
                # Check if mount process is still running
                if self.mount_process and self.mount_process.poll() is None:
                    logger.debug("Mount process is still active")
                    
                    # Periodically sync files to shared volume
                    if time.time() - last_sync >= sync_interval:
                        self.copy_files_to_shared_volume()
                        last_sync = time.time()
                        
                else:
                    logger.warning("Mount process ended, but keeping container alive...")
                    break
                
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
        
        # Keep container alive even if mount fails
        logger.info("Entering keep-alive mode...")
        while self.running:
            try:
                time.sleep(60)
                logger.debug("Sidecar still running...")
            except KeyboardInterrupt:
                break
    
    def run(self) -> None:
        """Main execution method."""
        logger.info("Starting GCS FUSE sidecar...")
        
        try:
            self.install_gcsfuse()
            self.create_mount_point()
            self.mount_bucket()
            self.copy_files_to_shared_volume()
            self.monitor_mount()
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            logger.info("GCS FUSE sidecar shutting down")

if __name__ == "__main__":
    manager = GCSFuseManager()
    manager.run()
