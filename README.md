# bandori-cards

A skill for [OpenClaw](https://github.com/openclaw/openclaw) to search for BanG Dream! Girls Band Party cards using the [bandori.party](https://bandori.party/) API.

## Features
- Search by character name (English or Japanese).
- Filter by rarity (1-5 stars).
- Get high-quality art URLs (Normal, Trained, and Transparent).
- Detailed card information including skills and attributes.

## Installation for OpenClaw
1. Copy the `scripts/get_bandori_card.py` to your OpenClaw workspace's `skills/bandori-cards/scripts/` directory.
2. Ensure you have `requests` installed: `pip install requests`.

## Usage
Run the script directly:
```bash
python3 scripts/get_bandori_card.py [query] [--rarity R] [--member MEMBER]
```

### Examples
- `python3 scripts/get_bandori_card.py Yukina`
- `python3 scripts/get_bandori_card.py Sayo --rarity 5`

## Credits
Data provided by [bandori.party](https://bandori.party/).
