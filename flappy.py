import pygame 
import neat 
import time
import os 
import random 
import socket 
import json 
import threading

pygame.font.init()
#pygame.init()  # Initialize Pygame

generation = 0  # Initialize generation counter
exchange_interval = 10  # Exchange genomes every 10 generations
threshold_fitness = 100  # 
host_name = ""

WIN_WIDTH = 550
WIN_HEIGHT = 800 

BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))
]

PIPE_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))]
BASE_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))]
BG_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))]
STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20 
    ANIMATION_TIME = 5 

    def __init__(self, x, y ):
        self.x = x
        self.y = y 
        self.tilt_count = 0
        self.tilt = 0 
        self.vel = 0 
        self.height = self.y 
        self.img_count = 0 
        self.img = self.IMGS[0]
        self.tick_count = 0 

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0 
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5 * self.tick_count**2 
        
        if d >= 16:
            d = 16

        if d < 0:
            d -= 2 
        
        self.y = self.y + d 

        if d < 0 or self.y < self.height + 50 :
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
        
    def draw(self, win):
        self.img_count += 1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]     
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]   
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]   
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]   
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]   
            self.img_count = 0 
        
        if self.tilt <= -80:
            self.img_count = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2 
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x,self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200;
    VEL =  5

    def __init__(self,x):
        self.x = x 
        self.height = 0 
        self.top = 0 
        self.bottom = 0 
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMGS[0], False, True)
        self.PIPE_BOTTOM = PIPE_IMGS[0]
        self.passed = False 
        self.set_height()
        self.tick_count = 0  # Add this line

    def set_height(self):
        self.height = random.randrange(50,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
    
    def move(self):
        self.x -= self.VEL
    
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask =  pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask =  pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        
        return False 

class Base:
    VEL = 5
    WIDTH = BASE_IMGS[0].get_width()
    IMG = BASE_IMGS

    def __init__(self, y ):
        self.y = y 
        self.x1 = 0 
        self.x2 = self.WIDTH
    
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0 :
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0 :
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG[0], (self.x1, self.y))
        win.blit(self.IMG[0], (self.x2,self.y))

def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMGS[0], (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()

def serialize_genome(genome):
    """
    Serialize the genome to a JSON-serializable format.
    """
    serialized_genome = {
        "key": genome.key,
        "fitness": genome.fitness,
        "nodes": [{k: v for k, v in node.__dict__.items()} for node in genome.nodes.values()],
        "connections": [{k: v for k, v in conn.__dict__.items()} for conn in genome.connections.values()]
    }
    return serialized_genome

def send_genomes(genomes_list, host, port):
    """
    Send genomes to the specified host and port using socket communication.
    """
    def send_thread():
        s = None  # Initialize socket variable
        try:
            # Connect to the host and port
            print("SENDING")
            s = socket.create_connection((host, port), timeout=1)
            for genome_key, genome in genomes_list:
                # Serialize the genome
                serialized_genome = serialize_genome(genome)
                # Send the serialized genome over the socket
                s.sendall(json.dumps(serialized_genome).encode())
        except socket.timeout:
            print("Connection to Scala host timed out.")
        except ConnectionRefusedError:
            print("Connection to Scala host refused.")
        except Exception as e:
            print("Error sending genomes:", e)
        finally:
            if s:  # Check if socket exists before closing
                s.close()
    thread = threading.Thread(target=send_thread)
    thread.start()

def receive_genomes(host, port):
    """
    Receive genomes from the Scala server.
    """
    received_genomes = None

    def receive_thread():
        nonlocal received_genomes
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                s.listen()
                conn, addr = s.accept()
                print("RECEIVING GENOMES")
                with conn:
                    data = b''
                    while True:
                        packet = conn.recv(4096)
                        if not packet:
                            break
                        data += packet
                    received_genomes = json.loads(data.decode())
        except Exception as e:
            print("Error receiving genomes:", e)

    thread = threading.Thread(target=receive_thread)
    thread.start()
    thread.join(timeout=1)  # Adjust the timeout value as needed

    return received_genomes


def main(genomes, config):
    global generation  
    host = "Jomos-MBP.lan"
    port_send = 8080
    port_receive = 8081
    generation += 1  

    # Game simulation and NEAT training
    nets = []
    ge = []
    birds = []

    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    score = 0
    clock = pygame.time.Clock()
        
    send_genomes_list = []
    received_genomes = []
    
    # Iterate over genomes
    for genome_key, g in genomes:
        g.fitness = 0.1  # Initialize fitness to 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(g)
        # Append genome key to list for sending
        send_genomes_list.append((genome_key, g))

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break
        # Iterate over birds
        for x, bird in enumerate(birds):
            if ge[x]:  # Check if the genome exists
                ge[x].fitness += 0.1
            bird.move()

            # Use the neural network to make decisions
            output = nets[birds.index(bird)].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()
        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    if ge[x]:  # Check if the genome exists
                        ge[x].fitness -= 1
                    birds.pop(x)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()
        if add_pipe:
            score += 1
            for g in ge:
                if g:  # Check if the genome exists
                    g.fitness += 5
            pipes.append(Pipe(700))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                if ge[x]:  # Check if the genome exists
                    birds.pop(x)

        draw_window(win, birds, pipes, base, score)

        # Send genomes to Scala/Akka node
        send_genomes(send_genomes_list, host, port_send)

        # Receive genomes from Scala/Akka node
        received_genomes = receive_genomes(host, port_receive)

        # Integrate received genomes into the population
        if received_genomes:
            for received_genome in received_genomes:
                genomes.append(received_genome)

    pygame.quit()  # Quit pygame when the loop exits

def run(config_path):
    #pygame.init()  # Initialize Pygame
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_path)
    p = neat.Population(config)  
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)

    pygame.quit()  

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat_config.txt")
    run(config_path)
