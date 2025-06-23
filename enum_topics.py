#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List Telegram forum topics from a group.
This script retrieves and lists all forum topics from a specified Telegram group.
It requires a valid Telegram API ID and API Hash, which can be provided via command line arguments
or loaded from a configuration file (config.yaml).
"""
import argparse
import asyncio
import yaml
from telethon import TelegramClient, functions


async def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


async def main():
    parser = argparse.ArgumentParser(description="List Telegram forum topics from a group.")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)")
    parser.add_argument("--api-id", type=int, help="Telegram API ID (overrides config.yaml)")
    parser.add_argument("--api-hash", type=str, help="Telegram API Hash (overrides config.yaml)")
    parser.add_argument("--group", required=True, help="Telegram group username or ID (e.g., @peass_group)")

    args = parser.parse_args()

    # Load config file
    config = await load_config(args.config)

    # Determine API credentials (from CLI or config)
    api_id = args.api_id if args.api_id else config["telegram"]["api_id"]
    api_hash = args.api_hash if args.api_hash else config["telegram"]["api_hash"]

    # Check if API credentials are provided
    if not api_id or not api_hash:
        raise ValueError("API ID and API Hash must be provided either via command line or config.yaml")

    print(f"Using API ID: {api_id} and API Hash: {api_hash}")

    group_username = args.group

    async with TelegramClient('session', api_id, api_hash) as client:
        try:
            entity = await client.get_entity(group_username)
            result = await client(functions.channels.GetForumTopicsRequest(
                channel=entity,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100,  # Adjust limit as needed
            ))

            print(f"\nTopics in group: {entity.title} (@{entity.username})\n")
            for topic in result.topics:
                print(f"ID: {topic.id} | Title: {topic.title}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
