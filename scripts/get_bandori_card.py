import requests
import sys
import argparse
import re
from concurrent.futures import ThreadPoolExecutor

# API 终端
MEMBER_API = "https://bandori.party/api/members/"
CARD_API = "https://bandori.party/api/cards/"

# 别名映射
NAME_ALIASES = {
    "rana": "Raana",
    "rana kaname": "Raana Kaname",
    "raana": "Raana",
    "kasumi": "Kasumi Toyama",
    "anon": "Anon Chihaya",
}

def get_member_info():
    """获取所有成员数据以构建映射"""
    members = []
    url = MEMBER_API
    while url:
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            members.extend(data.get('results', []))
            url = data.get('next')
        except:
            break
    
    id_map = {m['id']: m for m in members}
    name_map = {}
    for m in members:
        full_name = m.get('name', '').lower()
        jp_name = m.get('japanese_name', '').lower()
        name_map[full_name] = m['id']
        name_map[jp_name] = m['id']
        first_name = full_name.split(' ')[0] if ' ' in full_name else full_name
        if first_name not in name_map:
            name_map[first_name] = m['id']
            
    for alias, target in NAME_ALIASES.items():
        target_l = target.lower()
        if target_l in name_map:
            name_map[alias] = name_map[target_l]
            
    return id_map, name_map

def fetch_card_images(card_id):
    """
    核心改进：从 HTML 详情页打捞所有真实的图片路径。
    注意：有些链接可能是相对路径（以 /u/c/art/ 开头），需要补全。
    """
    url = f"https://bandori.party/card/{card_id}/"
    try:
        resp = requests.get(url, timeout=10)
        html = resp.text
        
        # 匹配所有包含路径的片段
        pattern = rf'/(?:u/c/art/)(?:a/)?{card_id}[^"\s>\']+'
        matches = list(set(re.findall(pattern, html)))
        
        normal_art = None
        trained_art = None
        
        # 排除缩略图 (tthumb)
        valid_matches = [m for m in matches if "/tthumb/" not in m]
        
        for m in valid_matches:
            # 补全协议和域名
            path = m if m.startswith('/') else f'/{m}'
            full_url = f"https://i.bandori.party{path}"
            
            if "/art/a/" in path:
                trained_art = full_url
            elif "/art/" in path:
                normal_art = full_url
        
        return normal_art, trained_art
    except:
        return None, None

def search_cards(query_terms, member_ids=None, rarity=None):
    """利用 API 搜索符合条件的卡片 ID"""
    params = {'page_size': 50}
    if query_terms:
        # 如果 query 是纯数字，尝试作为 ID 搜索
        if query_terms[0].isdigit():
            try:
                resp = requests.get(f"{CARD_API}{query_terms[0]}/", timeout=10)
                if resp.status_code == 200:
                    return [resp.json()]
            except:
                pass
        params['search'] = query_terms[0]
    elif member_ids:
        params['member'] = member_ids[0]
        
    try:
        resp = requests.get(CARD_API, params=params, timeout=10)
        results = resp.json().get('results', [])
        
        filtered = []
        for c in results:
            if member_ids and c.get('member') not in member_ids: continue
            if rarity and str(c.get('i_rarity')) != str(rarity): continue
            
            # 进一步过滤关键词
            match = True
            c_full = (f"{c.get('name', '')} {c.get('japanese_name', '')}").lower()
            for t in query_terms:
                if t not in c_full:
                    match = False
                    break
            if match:
                filtered.append(c)
        return filtered[:5] # 最多展示 5 张
    except:
        return []

def process_card(card, member_id_map):
    """单个卡片的完整处理逻辑（包含并行抓取图片）"""
    card_id = card['id']
    member = member_id_map.get(card.get('member'), {})
    
    # 基础信息
    rarity_stars = "★" * card.get('i_rarity', 0)
    title = card.get('japanese_name') or card.get('name') or "无题"
    jp_name = member.get('japanese_name', member.get('name', '不明'))
    band = member.get('i_band', 'N/A')
    attr = card.get('i_attribute', 'N/A')
    
    # 获取真实链接
    normal, trained = fetch_card_images(card_id)
    
    return {
        "id": card_id,
        "title": title,
        "rarity": rarity_stars,
        "character": jp_name,
        "band": band,
        "attribute": attr,
        "normal": normal,
        "trained": trained
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="*")
    parser.add_argument("--rarity")
    args = parser.parse_args()
    
    if not args.query:
        return

    # 1. 准备成员映射
    id_map, name_map = get_member_info()
    
    # 2. 解析查询
    member_ids = []
    other_terms = []
    for q in args.query:
        ql = q.lower()
        if ql in name_map:
            member_ids.append(name_map[ql])
        else:
            other_terms.append(ql)
            
    # 3. 搜索卡片
    cards = search_cards(other_terms, member_ids=member_ids, rarity=args.rarity)
    
    if not cards:
        print("カードが見つかりませんでした♪")
        return

    # 4. 并行处理图片抓取（提高速度）
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda c: process_card(c, id_map), cards))

    # 5. 输出
    for res in results:
        print(f"【 {res['rarity']} {res['title']} 】")
        print(f"キャラクター：{res['character']}")
        print(f"バンド：{res['band']}")
        print(f"属性：{res['attribute']}")
        print(f"詳細：https://bandori.party/card/{res['id']}/")
        
        if res['normal']:
            print(f"カードイラスト：{res['normal']}")
        if res['trained']:
            print(f"特訓後イラスト：{res['trained']}")
        print("-" * 40)

if __name__ == "__main__":
    main()
