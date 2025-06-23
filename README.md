# TeleSiphon 📡

**TeleSiphon** is a lightweight and flexible Telegram feed relay tool.

It connects to specific Telegram groups, channels, or topics (including forum
topics), monitors new messages, and forwards them automatically to an external
channel via Incoming Webhook. Currently, it supports Slack as the output target.

---

## Features

- Supports Telegram Supergroups and Topics (Forum threads)
- Supports multiple source channels/topics
- Slack Webhook integration
- YAML configuration file
- Easily extensible for future output targets (Discord, Web APIs, etc.)

---

## Requirements

- Python 3.x
- Telegram API credentials (API ID and API Hash from [my.telegram.org](https://my.telegram.org))
- Slack Webhook URL

---

## Installation

```bash
git clone https://github.com/y0k4i-1337/telesiphon.git
cd telesiphon
poetry install
```

## Configuration

Copy the `config.example.yaml` file to `config.yaml` and fill in your
Telegram API credentials and Slack Webhook URL, as well as the channels
you want to monitor.

In order to find the topic IDs, you can use the `enum_topics.py` script:

```bash
poetry run ./enum_topics.py --group @monitored_group
```

Take note of the topic IDs you want to monitor and add them to your `config.yaml`.

## Running the Application

To run the application, use the following command:

```bash
poetry run python ./telesiphon.py -v
```

By default, it will retrieve the messages from the current date. You can also
specify a limit on the number of messages to retrieve using the `--limit`
option, in which case the application will retrieve the latest messages
up to the specified limit. Finally, you can specify an offset id to
retrieve messages starting from a specific message ID using the `--offset-id`.

The script will write a state file to keep track of the last processed message.
When you run the script again, it will continue from where it left off, if no
`--offset-id` is specified.
