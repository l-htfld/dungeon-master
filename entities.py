class Entity:
    def __init__(self, hp=0, power=0) -> None:
        self.hp = hp
        self.power = power

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        print(f"{self.__class__.__name__} погиб")

class Hero(Entity):
    def __init__(self, hp=0, power=0, protect=0) -> None:
        super().__init__(hp, power)
        self.protect = protect

    def attack(self, target):
        damage = self.power - target.protect
        if damage > 0:
            target.take_damage(damage)
        else:
            print(f"{target.__class__.__name__} заблокировал атаку!")
            if self.hp == 0:
                print('Стоп')

class Enemy(Entity):
    def __init__(self, hp=0, power=0, protect=0) -> None:
        super().__init__(hp, power)
        self.protect = protect