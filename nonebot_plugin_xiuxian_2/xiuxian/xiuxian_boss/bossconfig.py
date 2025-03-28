configkey = ["Boss灵石", "Boss名字", "Boss倍率", "Boss个数上限", "Boss生成时间参数", 'open', "世界积分商品"]
CONFIG = {
    "open": {},
    "Boss灵石": {
        # 生成Boss给的灵石
        '炼体境': [500, 700, 980],
        '感气境': [1000, 1400, 1960],
        '引气境': [2000, 2800, 3920],
        '凝气境': [3000, 4200, 5880],
        '聚元境': [6000, 8400, 11760],
        '归元境': [12000, 16800, 23520],
        '通玄境': [24000, 33600, 47040],
        '踏虚境': [80000, 112000, 156800],
        '天人境': [180000, 252000, 352800],
        '悟道境': [340000, 476000, 666400],
        '炼神境': [600000, 840000, 1176000],
        '逆虚境': [1000000, 1400000, 1960000],
        '合道境': [3000000, 4200000, 5880000],
        '虚劫境': [5000000, 8200000, 11760000],
        '羽化境': [10000000, 14000000, 19600000],
        '登仙境': [18000000, 25200000, 35280000],
        '凡仙境': [30000000, 42000000, 58800000],
        '地仙境': [50000000, 70000000, 98000000],
        '玄仙境': [80000000, 90000000, 120000000],
        '金仙境': [180000000, 360000000, 1200000000],
    },
    "Boss名字": [
        "九寒",
        "精卫",
        "少姜",
        "陵光",
        "莫女",
        "术方",
        "卫起",
        "血枫",
        "以向",
        "砂鲛",
        "鲲鹏",
        "天龙",
        "莉莉丝",
        "霍德尔",
        "历飞雨",
        "神风王",
        "衣以候",
        "金凰儿",
        "元磁道人",
        "外道贩卖鬼",
        "散发着威压的尸体"
    ],  # 生成的Boss名字，自行修改
    "Boss个数上限": 45,
    "Boss倍率": {
        # Boss属性：大境界平均修为是基础数值，气血：15倍，真元：10倍，攻击力：0.2倍
        # 作为参考：人物的属性，修为是基础数值，气血：0.5倍，真元：1倍，攻击力：0.1倍
        "气血": 329,
        "真元": 20,
        "攻击": 8
    },
    "Boss生成时间参数": {  # Boss生成的时间，2个不可全为0
        "hours": 0,
        "minutes": 45
    },
    "世界积分商品": {
        "1": {
            "id": 1999,
            "cost": 10000,
            "desc": "渡厄丹,使下一次突破丢失的修为减少为0!"
        },
        "2": {
            "id": 4003,
            "cost": 5000,
            "desc": "陨铁炉,以陨铁炼制的丹炉,耐高温,具有基础的炼丹功能"
        },
        "3": {
            "id": 4002,
            "cost": 25000,
            "desc": "雕花紫铜炉,表面刻有精美雕花的紫铜丹炉,一看便出自大师之手,可以使产出的丹药增加1枚"
        },
        "4": {
            "id": 4001,
            "cost": 100000,
            "desc": "寒铁铸心炉,由万年寒铁打造的顶尖丹炉,可以使产出的丹药增加2枚"
        },
        "5": {
            "id": 2500,
            "cost": 5000,
            "desc": "一级聚灵旗,提升洞天福地中的灵气汇集速度,加速修炼速度和灵田中药材生长速度"
        },
        "6": {
            "id": 2501,
            "cost": 10000,
            "desc": "二级聚灵旗,提升洞天福地中的灵气汇集速度,加速修炼速度和灵田中药材生长速度"
        },
        "7": {
            "id": 2502,
            "cost": 20000,
            "desc": "三级聚灵旗,提升洞天福地中的灵气汇集速度,加速修炼速度和灵田中药材生长速度"
        },
        "8": {
            "id": 2503,
            "cost": 40000,
            "desc": "四级聚灵旗,提升洞天福地中的灵气汇集速度,加速修炼速度和灵田中药材生长速度"
        },
        "9": {
            "id": 2504,
            "cost": 80000,
            "desc": "仙级聚灵旗,大幅提升洞天福地中的灵气汇集速度,加速修炼速度和灵田中药材生长速度"
        },
        "10": {
            "id": 2505,
            "cost": 160000,
            "desc": "无上聚灵旗,极大提升洞天福地中的灵气汇集速度,加速修炼速度和灵田中药材生长速度"
        },
        "11": {
            "id": 7085,
            "cost": 2000000,
            "desc": "冲天槊，无上仙器，不属于这个位面的武器，似乎还有种种能力未被发掘...提升100%攻击力！提升50%会心率！提升20%减伤率！提升50%会心伤害！"
        },
        "12": {
            "id": 8931,
            "cost": 2000000,
            "desc": "苍寰变，无上神通，不属于这个位面的神通，连续攻击两次，造成6.5倍！7倍伤害！消耗气血0%、真元70%，发动概率100%，发动后休息一回合 "
        },
        "13": {
            "id": 9937,
            "cost": 2000000,
            "desc": "一气化三清，无上仙法，比上面几个还厉害，可惜太长写不下 "
        },
        "14": {
            "id": 10402,
            "cost": 700000,
            "desc": "真神威录，天阶下品辅修功法，增加70%会心率！"
        },
        "15": {
            "id": 10403,
            "cost": 1000000,
            "desc": "太乙剑诀，天阶下品辅修功法，增加100%会心伤害！"
        },
        "16": {
            "id": 10411,
            "cost": 1200000,
            "desc": "真龙九变，天阶上品辅修功法，增加攻击力60%！"
        }
    }
}
