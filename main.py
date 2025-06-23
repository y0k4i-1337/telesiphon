#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import asyncio
import datetime
import os
import yaml
import aiohttp
from telethon import TelegramClient, utils, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetForumTopicsByIDRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, InputPeerChat

STATE_FILE = "state.yaml"

"""Load configuration from a YAML file."""
async def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


"""Load state from a YAML file."""
async def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        return {}


"""Save state to a YAML file."""
async def save_state(state):
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f)


async def send_to_slack(webhook_url, message_text):
    async with aiohttp.ClientSession() as session:
        payload = {"text": message_text}
        async with session.post(webhook_url, json=payload) as resp:
            if resp.status != 200:
                print(f"Slack error: {resp.status} {await resp.text()}")



async def fetch_topic_messages(api_id, api_hash, group_username, topic_id, offset_id=0, limit=None):
    messages = []
    async with TelegramClient("session", api_id, api_hash) as client:
        try:
            # Get the group entity
            group_entity = await client.get_entity(group_username)

            offset_date = None
            reverse = False
            if offset_id == 0 and limit is None:
                # Get the current date in UTC and set the time to midnight (00:00)
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                current_date = now_utc.date()
                offset_date = datetime.datetime.combine(
                    current_date,
                    datetime.time.min,
                    tzinfo=datetime.timezone.utc,
                )
                limit = 10  # Default limit if not specified

            if offset_id > 0 or offset_date is not None:
                reverse = True

            if offset_id > 0 and limit is None:
                limit = 42

            messages = await client.get_messages(
                group_entity,
                reply_to=topic_id,
                limit=limit,
                offset_id=offset_id,
                offset_date=offset_date,
                reverse=reverse,
            )

            # print(
            #     (
            #         f"Retrieved {len(messages)} of {messages.total} messages "
            #         f"from topic {topic_id} in group {group_username}"
            #     )
            # )

            messages = sorted(messages, key=lambda m: m.date)

        except Exception as e:
            print(f"Error: {e}")
            messages = []
    return (group_entity.title, messages)

async def main():
    parser = argparse.ArgumentParser(
        description="Fetch last messages from a Telegram topic (async version)"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to config.yaml (default: config.yaml)",
    )
    parser.add_argument(
        "--api-id", type=int, help="Telegram API ID (overrides config.yaml)"
    )
    parser.add_argument(
        "--api-hash", type=str, help="Telegram API Hash (overrides config.yaml)"
    )
    parser.add_argument(
        "--offset-id",
        type=int,
        default=0,
        help="Start from this message ID (default: 0)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of messages to fetch (default: None)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Load config file
    config = await load_config(args.config)

    api_id = args.api_id if args.api_id else config["telegram"]["api_id"]
    api_hash = (
        args.api_hash if args.api_hash else config["telegram"]["api_hash"]
    )

    # Check if API credentials are provided
    if not api_id or not api_hash:
        raise ValueError(
            "API ID and API Hash must be provided either via command line "
            "or config.yaml"
        )

    # For each source in config, fetch messages from the specified topic
    if not config.get("sources"):
        raise ValueError("No sources found in config.yaml")

    state = await load_state()
    for source in config["sources"]:
        if "type" not in source:
            raise ValueError("Source configuration is missing 'type'")
        if source["type"] == "group_topic":
            if "group" not in source or "topic_id" not in source:
                raise ValueError(
                    (
                        "Source configuration for 'group_topic' must include "
                        "'group' and 'topic_id'"
                    )
                )
            group = source["group"]
            topic_id = source["topic_id"]
            source_key = f"{group}:{topic_id}"
            offset_id = args.offset_id
            if offset_id == 0:
                offset_id = state.get("group_topics", {}).get(source_key, 0)
            print(
                f"Fetching messages from group: {group}, "
                f"topic ID: {topic_id}, offset_id: {offset_id}"
            )
            topic, messages = await fetch_topic_messages(
                api_id,
                api_hash,
                group,
                topic_id,
                offset_id=offset_id,
                limit=args.limit,
            )
            if args.verbose:
                print(f"Retrieved {len(messages)} messages from topic {topic_id} in group {group}")
            for message in messages:
                if message.text:
                    if args.verbose:
                        print(
                            f"Message {message.id} from {message.sender_id}: "
                            f"{message.text}"
                        )
                    # Send message to Slack if configured (slack.webhook_url is
                    # set in config.yaml)
                    if "slack" in config and "webhook_url" in config["slack"]:
                        slack_text = (
                            f"*{topic}*\n\n"
                            f"{message.text}"
                        )
                        await send_to_slack(
                            config["slack"]["webhook_url"],
                            slack_text,
                        )
                        if args.verbose:
                            print(f"Sent message {message.id} to Slack")

            # Get id from the last message
            if messages:
                last_message_id = messages[-1].id
                state.setdefault("group_topics", {})[source_key] = last_message_id
                await save_state(state)
        else:
            print(f"Skipping unsupported source type: {source['type']}")


if __name__ == "__main__":
    asyncio.run(main())
