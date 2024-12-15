class Player:
    def __init__(self, hp):
        self.hp = hp
        self.atk_dg = 1
    def atk(self, enemy):
        enemy.hp -= self.atk_dg

fight_dict = {}
no = 1
for hp in [100, 200]:
    fight_dict[no] = Player(hp)
    no += 1
while fight_dict[1].hp:
    for no in [1, 2]:
        print(fight_dict[no].hp)
        fight_dict[no].atk(fight_dict[1])