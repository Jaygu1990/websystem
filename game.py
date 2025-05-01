import pygame
import random

# Initialize
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pikachu Random Walker")
clock = pygame.time.Clock()

# Load image
pikachu = pygame.image.load('static/Pokemon_images/pikachu.png')  # Make sure you have pikachu.png in the same folder!
pikachu = pygame.transform.scale(pikachu, (50, 50))  # Resize if needed

# Starting position
x, y = random.randint(0, 750), random.randint(0, 550)

# Main Loop
running = True
while running:
    screen.fill((255, 255, 255))  # White background

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Random walk
    x += random.choice([-20, -10, 0, 10, 20])
    y += random.choice([-20, -10, 0, 10, 20])

    # Keep inside screen
    x = max(0, min(x, 750))
    y = max(0, min(y, 550))

    screen.blit(pikachu, (x, y))
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
