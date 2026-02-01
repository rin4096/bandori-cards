import requests
import sys
import argparse
import concurrent.futures

MEMBER_API = "https://bandori.party/api/members/"
CARD_API = "https://bandori.party/api/cards/"

NAME_ALIASES = {
    "rana": "Raana",
    "rana kaname": "Raana Kaname",
    "raana": "Raana",
    "kasumi": "Kasumi Toyama",
    "anon": "Anon Chihaya",
}

def get_all_members():
    members = []
    url = MEMBER_API
    while url:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            members.extend(data.get('results', []))
            url = data.get('next')
        except:
            break
    return members

def build_member_maps(members):
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
    for alias, target in NAME_ALIASES.items():
        target_lower = target.lower()
        if target_lower in name_map:
            name_map[alias.lower()] = name_map[target_lower]
    return id_map, name_map

def verify_url(url):
    if not url: return None
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200: return url
    except: pass
    return None

def search_cards(query_terms, member_ids=None, rarity=None):
    cards = []
    url = CARD_API
    params = {'page_size': 100}
    if query_terms: params['search'] = query_terms[0]
    elif member_ids: params['member'] = member_ids[0]

    pages_to_fetch = 10
    current_page = 0
    while url and current_page < pages_to_fetch:
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            results = data.get('results', [])
            for card in results:
                if member_ids and card.get('member') not in member_ids: continue
                if rarity and str(card.get('i_rarity')) != str(rarity): continue
                card_name = (card.get('name') or "").lower()
                card_jp = (card.get('japanese_name') or "").lower()
                match = True
                for term in query_terms:
                    if term not in card_name and term not in card_jp:
                        match = False
                        break
                if match: cards.append(card)
            url = data.get('next')
            params = {}
            current_page += 1
            if len(cards) >= 10: break
        except: break
    return cards

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="*")
    parser.add_argument("--rarity")
    args = parser.parse_args()
    if not args.query: return

    members_data = get_all_members()
    id_map, name_map = build_member_maps(members_data)
    member_ids, remaining_terms = [], []
    for q in args.query:
        ql = q.lower()
        if ql in name_map: member_ids.append(name_map[ql])
        else: remaining_terms.append(ql)

    cards = search_cards(remaining_terms, member_ids=member_ids if member_ids else None, rarity=args.rarity)
    if not cards:
        print("カードが見つかりませんでした♪")
        return

    for card in cards[:3]:
        member = id_map.get(card.get('member'), {})
        jp_name = member.get('japanese_name', '不明')
        band_name = member.get('i_band', 'N/A')
        
        rarity_stars = "★" * card.get('i_rarity', 0)
        card_title = card.get('japanese_name') or card.get('name') or '无题'
        
        print(f"【 {rarity_stars} {card_title} 】")
        print(f"キャラクター：{jp_name}")
        print(f"バンド：{band_name}")
        print(f"属性：{card.get('i_attribute', 'N/A')}")
        print(f"詳細：https://bandori.party/card/{card['id']}/")
        
        # Priority check for SOP: Normal first, then Trained
        normal_art = verify_url(card.get('art'))
        trained_art = verify_url(card.get('art_trained'))
        
        if normal_art: print(f"カードイラスト：{normal_art}")
        if trained_art: print(f"特訓後イラスト：{trained_art}")
        
        print("-" * 40)

if __name__ == "__main__":
    main()
