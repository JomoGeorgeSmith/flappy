import pygame 
import neat 
import time
import os 
import random 
import socket 
import json 
import threading
import pickle 

pygame.font.init()
pygame.init()  

received_data = b''  

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

class Node:
    def __init__(self, key):
        self.key = key
        self.bias = None
        self.response = None
        self.aggregation = None
        self.ntype = None  # You might need to set a default value or handle the absence of the key appropriately

def save_genome(genome, filename):
    print("Saving Genome")
    with open(filename, 'wb') as f:
        pickle.dump(genome, f)

def load_genome(filename):
    print("loading Genome from disk")
    with open(filename, 'rb') as f:
        genomes = pickle.load(f)
        return genomes

curr_dir = os.path.dirname(os.path.abspath(__file__))
relative_path = ''
save_path = os.path.join(curr_dir,  relative_path)
def request_genome(host, port):
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")
        
        # Send a request to receive the file
        client_socket.sendall("SEND_GENOME".encode())
        
        # Receive the "READY" message
        ready_message = client_socket.recv(1024)
        if ready_message.decode() == "READY\n":
            print("Received ready message. Starting file transfer...")
            
            # Open a file for writing
            file_path = save_path + "trained_genome.pkl"
            with open(file_path, "wb") as file:
                while True:
                    # Receive data from the server
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    # Write received data to the file
                    file.write(data)
            
            print("File received and saved successfully.")
            
            # Wait for confirmation message from server
            confirmation_message = client_socket.recv(1024)
            if confirmation_message.decode() == "GENOME_SENT\n":
                print("Server confirmed genome sent.")
                global genome_sent
                genome_sent = True
        else:
            print("Unexpected message received. Aborting file transfer.")
        
    except Exception as e:
        print("An error occurred:", e)
    
    finally:
        # Close the client socket
        client_socket.close()

genome_sent = False

def send_genome(filename, host, port):
    """
    Send a single genome file to the specified host and port using socket communication.
    """
    def send_genome_thread(filename, host, port):
        global genome_sent  # Access the outer scope variable
        try:
            if not genome_sent:  # Check if the genome has not been sent within the interval
                # Connect to the host and port
                print("SENDING GENOME:", filename)
                with socket.create_connection((host, port), timeout=1) as s:
                    # Open the file and read its contents
                    with open(filename, 'rb') as f:
                        data = f.read()
                    # Send the file contents over the socket
                    s.sendall(data)
                # Set the flag to indicate that the genome has been sent
                genome_sent = True
                print("Genome sent successfully.")
            else:
                print("Genome already sent within the interval.")
        except socket.timeout:
            print("Connection to Scala host timed out.")
        except ConnectionRefusedError:
            print("Connection to Scala host refused.")
        except Exception as e:
            print("Error sending genome:", e)

    # Start a new thread to send the genome file
    thread = threading.Thread(target=send_genome_thread, args=(filename, host, port))
    thread.start()

    # Start a new thread to send the genome file
    thread = threading.Thread(target=send_genome_thread, args=(filename, host, port))
    thread.start()

def main(genomes, config):
    global genome_sent
    pygame.font.init()
    pygame.init()  
    global generation  
    host = "Jomos-MBP.lan"
    port_send = 8080
    port_receive = 8081
    generation += 1  


    request_genome(host, port_receive)
    ee = False

    if ee:
            trained_genomes_filename = "trained_genome.pkl"
            if os.path.exists(trained_genomes_filename):
                trained_genomes = load_genome(trained_genomes_filename)
            else:
                trained_genomes = []

    else:
        # Load previously saved top genomes if available
        trained_genomes_filename = "trained_genome.pkl"
        if os.path.exists(trained_genomes_filename):
            trained_genomes = load_genome(trained_genomes_filename)
        else:
            trained_genomes = []

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
    
    # Use top genomes if available
    if trained_genomes:
        net = neat.nn.FeedForwardNetwork.create(trained_genomes, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        #g.fitness = 0
        ge.append(trained_genomes)
    else:
        # If no top genomes, continue with regular genomes
        for genome_key, g in genomes:
            # Initialize fitness to 0
            net = neat.nn.FeedForwardNetwork.create(g, config)
            nets.append(net)
            birds.append(Bird(230, 350))
            g.fitness = 0
            ge.append(g)


    score_threshold = 10
    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

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
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)


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
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        # if score > 10:
        #     break

        draw_window(win, birds, pipes, base, score)

        if score > 0 and score % 10 == 0:
            genome_sent = False
            send_genome('trained_genome.pkl', host, port_send)
            # save current winner
            # in a seperate thread send pkl file to scala host and delete pkl file after it is sent. 
                
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_path)
    p = neat.Population(config)  
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)
    save_genome(winner, "trained_genome.pkl")

    pygame.quit()  

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "neat_config.txt")
    run(config_path)
     
