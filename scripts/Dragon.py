import pygame
import random

class Dragon:
    def __init__(self, x, y):
        self.image = pygame.image.load("dragon.png")  # Replace "dragon.png" with the actual dragon image file
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2
        self.fire_cooldown = 0
        self.fire_cooldown_max = 60  # Set the cooldown time for fire breath

    def update(self, game):
        # Move the dragon (left-right movement for simplicity)
        self.rect.x += self.speed

        # Check screen boundaries to reverse direction
        if self.rect.left < 0 or self.rect.right > 640:
            self.speed *= -1

        # Update fire cooldown timer
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        # Shoot fire if the cooldown is over and randomly triggered
        if self.fire_cooldown == 0 and random.randint(0, 100) < 3:
            self.shoot_fire(game)

    def shoot_fire(self, game):
        # Code to create fire projectiles, you can customize this part as needed
        fire_projectile = FireProjectile(self.rect.centerx, self.rect.centery)
        game.all_projectiles.append(fire_projectile)

        # Reset the fire cooldown
        self.fire_cooldown = self.fire_cooldown_max

    def render(self, screen, offset):
        # Draw the dragon on the screen
        screen.blit(self.image, [self.rect.centerx - offset[0], self.rect.centery - offset[1]])


class FireProjectile:
    def __init__(self, x, y):
        self.image = pygame.Surface((10, 5))
        self.image.fill((255, 0, 0))  # Red color for simplicity, replace with the actual fire image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5

    def update(self):
        # Move the fire projectile vertically
        self.rect.y -= self.speed

    def render(self, screen, offset):
        # Draw the fire projectile on the screen
        screen.blit(self.image, [self.rect.centerx - offset[0], self.rect.centery - offset[1]])
