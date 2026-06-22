#!/usr/bin/env python3

import os
import sys
import yaml
import time
from pathlib import Path
from config import Config
from controllers.couchbase_controller import CouchbaseController
from utils.logger import get_logger

def get_env_var(name, default=None):
    """Get environment variable with optional default."""
    try:
        if default is not None:
            return os.environ.get(name, default)
        else:
            return os.environ[name]
    except KeyError:
        raise KeyError(f"Environment variable '{name}' is not set")

def main():
    """Main entry point for the init module."""
    logger = get_logger('config-manager')

    logger.info("🚀 Starting config-manager...")

    try:
        # Get environment variables
        environment = get_env_var('ENVIRONMENT')
        logger.info(f"📊 Environment: {environment}")

        # Initialize config manager with hardcoded config path
        config_file_path = Path('conf/config.yaml')
        logger.info(f"📁 Config file path: {config_file_path}")

        config = Config(config_file_path, environment)

        # Validate environment
        if not config.is_valid_environment(environment):
            logger.error(f"❌ Invalid environment '{environment}' - not found in config file")
            sys.exit(1)

        logger.info(f"✅ Environment '{environment}' validated successfully")

        # Get available targets by detecting config files
        targets = config.get_targets()
        target_ids = list(targets.keys())

        if not target_ids:
            logger.warning("⚠️  No target config files found (couchbase.yaml/yml, redpanda.yaml/yml)")

        if target_ids:
            logger.info(f"🎯 Found {len(target_ids)} available target(s): {', '.join(target_ids)}")

        # Process each available target
        processed_count = 0

        if 'couchbase' in target_ids:
            logger.info("🔄 Processing Couchbase configuration...")
            couchbase_controller = CouchbaseController(environment, config)
            couchbase_controller.run_ops()
            processed_count += 1
            logger.info("✅ Couchbase processing completed")

        if target_ids:
            logger.info(f"🎉 Configuration processing completed! Completed {processed_count}/{len(target_ids)} targets")
        else:
            logger.info("ℹ️  No configurations to process.")

    except Exception as e:
        logger.error(f"💥 Fatal error in config-manager: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)

if __name__ == "__main__":
    main()
