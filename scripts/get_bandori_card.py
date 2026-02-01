import requests
import sys
import argparse
import json

MEMBER_API = "https://bandori.party/api/members/"
CARD_API = "https://bandori.party/api/cards/"

def get_all_members():
    members = []
    url = MEMBER_API
    while url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            members.extend(data.get('results', []))
            url = data.get('next')
        except Exception as e:
            print(f"Error fetching members: {e}", file=sys.stderr)
            break
    return members

def find_member_ids(query, members):
    query = query.lower()
    matching_ids = []
    for m in members:
        name = m.get('name', '').lower()
        jp_name = m.get('japanese_name', '').lower()
        if query in name or query in jp_name:
            matching_ids.append(m['id'])
    return matching_ids

def get_cards(member_ids=None, rarity=None, query=None):
    cards = []
    url = CARD_API
    
    # Simple pagination limit for speed in CLI
    pages_to_fetch = 5 
    current_page = 0
    
    while url and current_page < pages_to_fetch:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            
            for card in results:
                match = True
                
                if member_ids and card.get('member') not in member_ids:
                    match = False
                
                if rarity and str(card.get('i_rarity')) != str(rarity):
                    match = False
                
                if query:
                    q = query.lower()
                    name = (card.get('name') or "").lower()
                    jp_name = (card.get('japanese_name') or "").lower()
                    if q not in name and q not in jp_name:
                        match = False
                
                if match:
                    cards.append(card)
            
            url = data.get('next')
            current_page += 1
        except Exception as e:
            print(f"Error fetching cards: {e}", file=sys.stderr)
            break
            
    return cards

def main():
    parser = argparse.ArgumentParser(description="Search for BanG Dream! cards.")
    parser.add_argument("query", nargs="?", help="Search query (Character name or Card name)")
    parser.add_argument("--rarity", help="Filter by rarity (1-5)")
    parser.add_argument("--member", help="Filter specifically by member name")
    
    args = parser.parse_args()
    
    members = get_all_members()
    member_map = {m['id']: m for m in members}
    
    member_ids = []
    if args.member:
        member_ids = find_member_ids(args.member, members)
    elif args.query:
        # Check if the query matches a member name
        member_ids = find_member_ids(args.query, members)

    # If query was meant for card name and didn't match any member, 
    # we don't restrict by member_id but search in name.
    # If it matched a member, we filter by that member.
    
    cards = get_cards(member_ids=member_ids if member_ids else None, 
                     rarity=args.rarity, 
                     query=args.query if not member_ids else None)

    if not cards:
        print("No cards found.")
        return

    for card in cards:
        member = member_map.get(card.get('member'), {})
        member_name = member.get('name', 'Unknown')
        
        print("-" * 30)
        print(f"Name (EN): {card.get('name') or 'N/A'}")
        print(f"Name (JP): {card.get('japanese_name') or 'N/A'}")
        print(f"Character: {member_name}")
        print(f"Rarity:    {'★' * card.get('i_rarity', 0)}")
        print(f"Attribute: {card.get('i_attribute')}")
        print(f"Skill:     {card.get('full_skill') or card.get('skill_name') or 'N/A'}")
        print(f"Art:       {card.get('art')}")
        if card.get('art_trained'):
            print(f"Art Trained: {card.get('art_trained')}")
        print(f"Transparent: {card.get('transparent')}")
        print("-" * 30)

if __name__ == "__main__":
    main()
