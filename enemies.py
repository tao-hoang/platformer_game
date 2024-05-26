import pygame
import random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, platforms, player):
        super().__init__()
        #self.idle_frames = [pygame.image.load('assets/enemy/idle/0.png').convert_alpha(),
                 #           pygame.image.load('assets/enemy/idle/1.png').convert_alpha()]
        #self.running_frames = [pygame.image.load('assets/enemy/running/0.png').convert_alpha(),
                       #        pygame.image.load('assets/enemy/running/1.png').convert_alpha()]
       # self.attack_frames = [pygame.image.load('assets/enemy/attack/0.png').convert_alpha(),
                  #           pygame.image.load('assets/enemy/attack/1.png').convert_alpha()]
        self.image = self.get_idle_image(0)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.change_x = 0
        self.change_y = 0
        self.platforms = platforms
        self.player = player
        self.idle_frame = 0
        self.running_frame = 0
        self.attack_frame = 0
        self.idle_animation_speed = 24
        self.running_animation_speed = 8
        self.attack_animation_speed = 12
        self.idle_animation_counter = 0
        self.running_animation_counter = 0
        self.attack_animation_counter = 0
        self.facing_right = True
        self.direction = 1  # 1 for right, -1 for left
        self.speed = 2
        self.gravity = 0.6
        self.attack_range = 100
        self.attacking = False
        self.attack_cooldown = 500  # milliseconds
        self.last_attack_time = 0
        self.health = 100  # Set initial health

    def get_idle_image(self, frame):
        idle_frame = pygame.Surface((33, 45), pygame.SRCALPHA).convert_alpha()
        idle_frame.blit(self.idle_frames[frame], (0, 0))
        return idle_frame

    def get_running_image(self, frame):
        running_frame = pygame.Surface((36, 42), pygame.SRCALPHA).convert_alpha()
        running_frame.blit(self.running_frames[frame], (0, 0))
        return running_frame

    def get_attack_image(self, frame):
        attack_frame = pygame.Surface((36, 42), pygame.SRCALPHA).convert_alpha()
        attack_frame.blit(self.attack_frames[frame], (0, 0))
        return attack_frame

    def update(self):
        self.calc_gravity()

        self.rect.x += self.change_x
        self.check_collision('x')

        self.rect.y += self.change_y
        self.check_collision('y')

        if self.attacking:
            self.attack_animation_counter += 1
            if self.attack_animation_counter >= self.attack_animation_speed:
                self.attack_animation_counter = 0
                self.attack_frame = (self.attack_frame + 1) % len(self.attack_frames)
                self.image = self.get_attack_image(self.attack_frame)
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)

                if self.attack_frame == len(self.attack_frames) - 1:
                    self.attacking = False

        elif abs(self.player.rect.x - self.rect.x) <= self.attack_range:
            self.attack()

        else:
            self.idle_animation_counter += 1
            if self.idle_animation_counter >= self.idle_animation_speed:
                self.idle_animation_counter = 0
                self.idle_frame = (self.idle_frame + 1) % len(self.idle_frames)
                self.image = self.get_idle_image(self.idle_frame)
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)

            self.running_animation_counter += 1
            if self.running_animation_counter >= self.running_animation_speed:
                self.running_animation_counter = 0
                self.running_frame = (self.running_frame + 1) % len(self.running_frames)
                self.image = self.get_running_image(self.running_frame)
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.image, True, False)

            self.patrol()

        # Check if the enemy is dead
        if self.health <= 0:
            self.kill()

    def calc_gravity(self):
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += self.gravity

    def patrol(self):
        if not self.attacking:
            self.change_x = self.direction * self.speed
            self.rect.x += self.change_x
            self.check_collision('x')

            # Reverse direction if at edge of platform or colliding with another platform
            if self.on_edge() or self.colliding():
                self.direction *= -1
                self.change_x = 0
                self.facing_right = not self.facing_right

    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            self.attacking = True
            self.attack_animation_counter = 0
            self.attack_frame = 0
            self.last_attack_time = current_time
            self.inflict_damage()

    def inflict_damage(self):
        if self.rect.colliderect(self.player.rect):
            self.player.take_damage(10)

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def check_collision(self, direction):
        if direction == 'x':
            collisions = pygame.sprite.spritecollide(self, self.platforms, False)
            for platform in collisions:
                if self.change_x > 0:
                    self.rect.right = platform.rect.left
                elif self.change_x < 0:
                    self.rect.left = platform.rect.right

        elif direction == 'y':
            collisions = pygame.sprite.spritecollide(self, self.platforms, False)
            for platform in collisions:
                if self.change_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.change_y = 0
                elif self.change_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.change_y = 0

    def on_edge(self):
        self.rect.x += self.direction * self.speed
        collision = pygame.sprite.spritecollideany(self, self.platforms)
        self.rect.x -= self.direction * self.speed
        return collision is None

    def colliding(self):
        return pygame.sprite.spritecollideany(self, self.platforms)

# Example player class with take_damage method
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.health = 100  # Example health

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
        print(f"Player health: {self.health}")
