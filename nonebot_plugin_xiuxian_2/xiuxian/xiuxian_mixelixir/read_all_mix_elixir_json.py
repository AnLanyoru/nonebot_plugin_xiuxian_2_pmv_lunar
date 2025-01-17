from ..xiuxian_utils.item_json import items

# 药性定义
herb_value_def = {
    -1: "性寒",
    0: "性平",
    1: "性热",
    2: "生息",
    3: "养气",
    4: "炼气",
    5: "聚元",
    6: "凝神"}

all_mix_elixir = {item_id: items_info
                  for item_id, items_info in items.items.items()
                  if items_info["item_type"] == '合成丹药'}

all_mix_elixir_table = {}
for mix_elixir_id, mix_elixir_info in all_mix_elixir.items():
    elixir_mix_type = [herb_value_def[int(here_type)]
                       for here_type in mix_elixir_info['elixir_config'].keys()].sort()
    need_power = sum(mix_elixir_info['elixir_config'].values())
    if elixir_mix_type in all_mix_elixir_table:
        all_mix_elixir_table[elixir_mix_type][need_power] = mix_elixir_id
    else:
        all_mix_elixir_table[elixir_mix_type] = {need_power: mix_elixir_id}
for mix_elixir_table in all_mix_elixir_table:
    all_mix_elixir_table[mix_elixir_table] = dict(sorted(all_mix_elixir_table[mix_elixir_table].items(),
                                                         key=lambda x: x[0], reverse=True))
