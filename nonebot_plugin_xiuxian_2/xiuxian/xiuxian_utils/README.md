### 战斗流程详细解释文档

#### 输入数据

- **player1**: 玩家1的数据，包含user_id、道号、气血、攻击、真元、会心、经验等信息。
- **player2**: 玩家2的数据，格式与player1相同。
- **type_in**: 战斗类型。
    - `1`：切磋，不消耗气血和真元。
    - `2`：正式战斗，消耗气血和真元。
- **bot_id**: 用于记录或输出的机器人ID。

#### 玩家数据初始化

1. **获取玩家Buff信息**：

    - 调用 `UserBuffDate()`获取玩家1和玩家2的buff信息。
    - 获取主Buff的数据：`get_user_main_buff_data()`，分别获取玩家的 `hpbuff`（气血增益）和 `mpbuff`（真元增益）。
    - 获取传承增益信息：使用 `xiuxian_impart.get_user_impart_info_with_id()`方法获取玩家的传承数据，进而计算额外的气血和真元增益，累加到各自的buff上。
2. **技能数据初始化**：

    - 检查玩家是否拥有技能：调用 `get_user_sec_buff_data()`获取玩家的技能数据，如果存在技能，则标记技能开启状态为 `True`。
3. **辅修功法数据初始化**：

    - 检查玩家是否拥有辅修功法：调用 `get_user_sub_buff_data()`获取玩家的辅修功法数据，如果存在辅修功法，则标记辅修功法开启状态为
      `True`。

#### 回合制战斗流程

1. **初始设置**：

    - 初始化 `play_list`用于记录每一步的战斗日志。
    - `isSql`用于判断是否为正式战斗（`type_in == 2`），如果是则需要更新数据库中的玩家状态。
    - `user1_turn_skip`和 `user2_turn_skip`用于标记玩家是否可以进行当前回合的操作。
    - 记录玩家初始气血值用于战斗日志的输出。
2. **战斗主循环**：

    - 进入 `while True`循环，玩家轮流进行攻击，直至某一方气血值小于等于零。
3. **玩家1的回合**：

    - **技能释放判断**：
        - 如果玩家1有技能且当前不需要跳过回合，输出当前回合信息并获取技能的气血消耗、真元消耗、技能类型和技能触发概率。
        - **技能释放**：根据技能类型分别处理：
            - **直接伤害技能**：直接对玩家2造成伤害，计算伤害值并应用减伤效果。
            - **持续性伤害技能**：对玩家2造成持续性伤害，每回合计算一次伤害值。
            - **Buff类技能**：可能增加攻击力或减伤效果，影响接下来的普通攻击或技能效果。
            - **封印技能**：使玩家2在接下来的若干回合内无法行动。
        - **普通攻击**：如果技能不满足释放条件，则执行普通攻击，判定是否暴击并计算伤害。
    - **辅修功法处理**：
        - 调用 `after_atk_sub_buff_handle()`处理辅修功法的效果，例如增加额外的伤害或回复。
    - **胜负判断**：如果玩家2的气血值小于等于零，则判定玩家1获胜并结束战斗。
4. **玩家2的回合**：

    - **技能释放判断**：与玩家1相同，判断玩家2是否可以释放技能，并根据技能类型分别处理。
    - **普通攻击**：如果技能无法释放，则执行普通攻击，计算伤害并应用减伤效果。
    - **辅修功法处理**：
        - 调用 `after_atk_sub_buff_handle()`处理玩家2的辅修功法效果。
    - **胜负判断**：如果玩家1的气血值小于等于零，则判定玩家2获胜并结束战斗。
5. **特殊情况处理**：

    - **双方无法行动**：如果两个玩家都因技能效果无法行动，输出相关日志并跳过该回合。
    - **逻辑错误检测**：如果双方气血值均小于等于零，则判定为逻辑错误并结束循环。

#### 战斗结束处理

- 根据战斗结果更新数据库中的玩家状态，主要更新气血和真元的数值。
- 返回 `play_list`（战斗日志）和 `suc`（胜利者的道号）。

#### 辅助函数说明

- **`get_skill_hp_mp_data()`**：用于获取技能消耗气血、真元、技能类型、技能释放概率。
- **`isEnableUserSikll()`**：判断玩家是否满足技能释放条件。
- **`get_turnatk()`**：计算玩家在当前回合的攻击力，判定是否暴击。
- **`calculate_skill_cost()`**：根据技能消耗更新玩家的气血和真元。
- **`get_persistent_skill_msg()`**：获取持续性技能的描述信息，用于战斗日志。
- **`after_atk_sub_buff_handle()`**：处理辅修功法在攻击后的效果，例如额外伤害或状态变化。

#### ST1和ST2字典说明

- **ST1和ST2**：定义了技能或状态的类型及其触发概率。
- **`get_st1_type()`** 和 `get_st2_type()`：根据概率返回对应的技能或状态类型，用于随机事件触发。

### Boss战斗流程详细解释文档

#### 输入数据

* **player1**: 玩家1的数据，包含user_id、道号、气血、攻击、真元、会心、经验等信息。
* **boss**: Boss的数据，包含名称、气血、攻击力、技能等信息。
* **type_in**: 战斗类型，默认为2，表示正式战斗。
* **bot_id**: 用于记录或输出的机器人ID。

#### 玩家数据初始化

1. **获取玩家Buff信息**：
    * 调用 `<span>UserBuffDate()</span>` 获取玩家的buff信息。
    * 如果玩家buff数据为空，设置主buff和辅修功法数据为空。
    * 如果玩家buff数据不为空，获取主buff数据、辅修功法数据，包含：
        * 气血增益（`<span>hpbuff</span>`）
        * 真元增益（`<span>mpbuff</span>`）
        * 随机增益（`<span>random_buff</span>`）
        * 辅修功法的不同类型增益（如 `<span>fan</span>`、`<span>stone</span>`、`<span>integral</span>`、
          `<span>break</span>`）
2. **获取玩家传承增益**：
    * 使用 ` <span>xiuxian_impart.get_user_impart_info_with_id()</span>` 获取玩家的传承数据，计算额外的气血和真元增益，并累加到各自的buff上。
3. **随机增益初始化**：
    * 如果玩家的随机增益开启，则根据随机数生成不同类型的增益：
        * **破甲**（`<span>random_break</span>`）：增加伤害穿透效果。
        * **吸血**（`<span>random_xx</span>`）：增加吸血效果。
        * **会心**（`<span>random_hx</span>`）：增加暴击概率。
        * **减伤**（`<span>random_def</span>`）：增加减伤效果。
4. **技能、辅修功法初始化**：
    * 获取玩家的技能数据，如果玩家有技能，则标记技能开启状态。
    * 获取玩家的辅修功法数据，如果存在辅修功法，则标记辅修功法开启状态。

#### Boss数据初始化

1. **Boss技能和减伤初始化**：
    * 根据Boss的境界（`jj`）确定Boss的初始减伤比例和技能效果。
    * Boss可以拥有不同的增益或减益效果，如：攻击增益、会心增益、暴伤增益、禁血等。
    * 还会随机选择Boss的神通类型，赋予Boss额外的技能效果，如降低玩家攻击、降低玩家会心、禁蓝等。
2. **Buff和技能数据初始化**：
    * 根据Boss的名称，如果其减伤小于等于0.6，则会显示其使用了某个技能来获得减伤的效果。
    * 初始化一些Boss的其他技能信息，如攻击增益、会心增益等。
    * 如果玩家有随机增益（例如破甲、吸血、减伤等），也会输出相应的日志信息。

#### 回合制战斗流程

1. **初始设置**：
    * 初始化 `play_list` 用于记录每一步的战斗日志。
    * `isSql` 用于判断是否为正式战斗，如果是则需要更新数据库中的玩家状态。
    * 初始化标志位，如玩家和Boss的行动跳过标志等。
    * 获取玩家的初始减伤值。
2. **战斗主循环**：
    * 进入 `while True` 循环，玩家和Boss轮流进行攻击，直至某一方气血值小于等于零。
3. **玩家的回合**：
    * **技能释放判断**：
        * 如果玩家有技能且不需要跳过回合，获取技能的气血消耗、真元消耗、技能类型和触发概率。
        * **技能释放**：根据技能类型分别处理：
            * **直接伤害技能**：对Boss造成直接伤害，计算伤害值并应用减伤和破甲效果。
            * **持续性伤害技能**：对Boss造成持续性伤害，每回合计算一次伤害值。
            * **Buff类技能**：可能增加攻击力或减伤效果，影响接下来的普通攻击或技能效果。
            * **封印技能**：使Boss在接下来的若干回合内无法行动。
        * **普通攻击**：如果技能不满足释放条件，则执行普通攻击，判定是否暴击并计算伤害。
    * **辅修功法处理**：
        * 调用 `after_atk_sub_buff_handle()` 处理辅修功法的效果，例如增加额外的伤害或回复。
    * **胜负判断**：如果Boss的气血值小于等于零，则判定玩家获胜并结束战斗。
4. **Boss的回合**：
    * **技能释放判断**：
        * 如果Boss不需要跳过回合，则随机选择使用技能或普通攻击。
        * 如果Boss使用技能，可能会增加攻击、会心率或暴击伤害等，或者直接对玩家造成伤害。
        * **普通攻击**：如果没有技能，Boss会执行普通攻击，并判定是否暴击。
    * **胜负判断**：如果玩家的气血值小于等于零，则判定Boss获胜并结束战斗。

#### 战斗结束处理

* 根据战斗结果更新数据库中的玩家状态，主要更新气血和真元的数值。
* 计算玩家获得的Boss掉落物品数量，并更新Boss的掉落物品数量。
* 返回 `play_list`（战斗日志）、`suc`（胜负结果）、`boss`（更新后的Boss状态）和 `get_stone`（玩家获得的灵石数量）。
