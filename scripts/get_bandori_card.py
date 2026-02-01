import requests
import sys
import argparse
import concurrent.futures

MEMBER_API = "https://bandori.party/api/members/"
CARD_API = "https://bandori.party/api/cards/"

# Static alias map for common alternative spellings
NAME_ALIASES = {
    "rana": "Raana",
    "rana kaname": "Raana Kaname",
    "raana": "Raana",
    "kasumi": "Kasumi Toyama",
    "anon": "Anon Chihaya",
}

def get_all_members():
    """Fetch all members to build a name-to-ID mapping."""
    members = []
    url = MEMBER_API
    while url:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            members.extend(data.get('results', []))
            url = data.get('next')
        except Exception as e:
            # print(f"Error fetching members: {e}", file=sys.stderr)
            break
    return members

def build_member_maps(members):
    """Build lookup maps for IDs and names."""
    id_map = {m['id']: m for m in members}
    name_map = {}
    for m in members:
        full_name = m.get('name', '').lower()
        jp_name = m.get('japanese_name', '').lower()
        first_name = full_name.split(' ')[0] if ' ' in full_name else full_name
        
        name_map[full_name] = m['id']
        name_map[jp_name] = m['id']
        if first_name not in name_map:
            name_map[first_name] = m['id']
            
    # Add manual aliases
    for alias, target in NAME_ALIASES.items():
        target_lower = target.lower()
        if target_lower in name_map:
            name_map[alias.lower()] = name_map[target_lower]
        else:
            for name, mid in name_map.items():
                if target_lower in name:
                    name_map[alias.lower()] = mid
                    break
            
    return id_map, name_map

def verify_url(url):
    """Verify if a URL is valid via HEAD request."""
    if not url:
        return None
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            ctype = resp.headers.get("Content-Type", "").lower()
            if "image" in ctype or "octet-stream" in ctype:
                return url
    except:
        pass
    return None

def search_cards(query_terms, member_ids=None, rarity=None):
    """Search for cards matching member IDs and other query terms."""
    cards = []
    url = CARD_API
    
    # We will search specifically by search keyword
    # The API 'search' parameter is the most reliable for finding cards by name
    params = {'page_size': 100}
    if query_terms:
        # Prioritize the "Sanrio" or similar keyword for the API search
        params['search'] = query_terms[0]
    elif member_ids:
        # Fallback to member-based API search if no other terms
        params['member'] = member_ids[0]

    pages_to_fetch = 10 
    current_page = 0

    while url and current_page < pages_to_fetch:
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            
            for card in results:
                # 1. Member Filter (Local)
                if member_ids and card.get('member') not in member_ids:
                    continue
                
                # 2. Rarity Filter
                if rarity and str(card.get('i_rarity')) != str(rarity):
                    continue

                # 3. Composite Keyword matching (Local)
                card_name = (card.get('name') or "").lower()
                card_jp = (card.get('japanese_name') or "").lower()
                
                match = True
                for term in query_terms:
                    if term not in card_name and term not in card_jp:
                        match = False
                        break
                
                if match:
                    cards.append(card)
            
            url = data.get('next')
            params = {} 
            current_page += 1
            if len(cards) >= 10:
                break
        except:
            break
            
    return cards

def main():
    parser = argparse.ArgumentParser(description="Search for BanG Dream! cards.")
    parser.add_argument("query", nargs="*", help="Search query (e.g., 'Kasumi Sanrio')")
    parser.add_argument("--rarity", help="Filter by rarity (1-5)")
    parser.add_argument("--member", help="Force filter by member name")
    args = parser.parse_args()
    
    if not args.query and not args.member:
        parser.print_help()
        return

    # 1. Build member maps
    members_data = get_all_members()
    id_map, name_map = build_member_maps(members_data)
    
    # 2. Identify member vs search terms
    member_ids = []
    remaining_terms = []
    
    # We'll use a simpler heuristic: if a word matches a member, it's a member ID filter.
    # Otherwise, it's a card name keyword.
    for q in args.query:
        ql = q.lower()
        if ql in name_map:
            member_ids.append(name_map[ql])
        else:
            remaining_terms.append(ql)

    if args.member:
        m_id = name_map.get(args.member.lower())
        if m_id:
            member_ids.append(m_id)

    # 3. Fetch cards
    cards = search_cards(remaining_terms, member_ids=member_ids if member_ids else None, rarity=args.rarity)

    if not cards:
        # Final fallback: if no cards found with composite, try searching ONLY member or ONLY keyword
        if member_ids and remaining_terms:
             # Try just the keyword
             cards = search_cards(remaining_terms, member_ids=None, rarity=args.rarity)
             # Then filter by member name string in card name as a hail mary
             if cards:
                 # Filter by member name if possible
                 pass 

    if not cards:
        print("No cards found matching your query.")
        return

    print(f"Found {len(cards)} card(s). Verifying images...\n")
    
    for card in cards[:5]:
        member = id_map.get(card.get('member'), {})
        member_name = member.get('name', 'Unknown')
        
        # Priority: art_trained > art > transparent_trained > transparent > image_trained > image
        links_to_check = {
            "Art (Trained)": card.get('art_trained'),
            "Art (Normal)": card.get('art'),
            "Transparent (Trained)": card.get('transparent_trained'),
            "Transparent (Normal)": card.get('transparent'),
            "Image (Trained)": card.get('image_trained'),
            "Image (Normal)": card.get('image')
        }
        
        valid_links = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(verify_url, url): label for label, url in links_to_check.items() if url}
            for future in concurrent.futures.as_completed(futures):
                label = futures[future]
                res = future.result()
                if res:
                    valid_links[label] = res

        # Output
        rarity_stars = "★" * card.get('i_rarity', 0)
        print(f"【 {rarity_stars} {card.get('name') or 'No Title'} 】")
        print(f"Character: {member_name} ({member.get('i_band', 'N/A')})")
        print(f"Attribute: {card.get('i_attribute', 'N/A')}")
        
        priority_order = ["Art (Trained)", "Art (Normal)", "Transparent (Trained)", "Transparent (Normal)", "Image (Trained)", "Image (Normal)"]
        found_any = False
        for label in priority_order:
            if label in valid_links:
                print(f"{label}: {valid_links[label]}")
                found_any = True
        
        if not found_any:
            # Last ditch: show unverified links
            for label in priority_order:
                if links_to_check[label]:
                    print(f"{label} (Unverified): {links_to_check[label]}")
                    found_any = True
                    break
                    
        print("-" * 40)

if __name__ == "__main__":
    main()
