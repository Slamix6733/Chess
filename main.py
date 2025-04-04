#For user input and handling gamestate

import pygame as p
import ChessEngine
import SmartMoveFinder
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT//DIMENSION

MAX_FPS = 15 #for animations
IMAGES = {}

CURRENT_THEME = "theme1"  # Default theme
THEMES = {
    "theme1": "Images/",
    "theme2": "Images2/"  # Path to your new theme images
}

# Load images based on selected theme
def loadImages(theme_path):
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'wP']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(theme_path + piece + ".png"), (SQ_SIZE, SQ_SIZE))
         #Note: We can access an image by saying 'IMAGES['up']'

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = p.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        p.draw.rect(screen, color, self.rect)
        
        font = p.font.SysFont("comicsansms", 20)
        text_surf = font.render(self.text, True, p.Color("black"))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click[0]

# Theme selection screen
def theme_selection_screen():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))
    p.display.set_caption("Chess Theme Selection")
    clock = p.time.Clock()
    
    # Create buttons
    theme1_button = Button(BOARD_WIDTH//2 - 150, BOARD_HEIGHT//2 - 60, 300, 50, "Lichess Theme", p.Color(181,135,99),p.Color(240,218,181) )
    theme2_button = Button(BOARD_WIDTH//2 - 150, BOARD_HEIGHT//2 + 10, 300, 50, "Chess.com Theme", p.Color(114,148,81), p.Color(236,236,208))
    
    running = True
    selected_theme = None
    
    while running:
        mouse_pos = p.mouse.get_pos()
        mouse_click = p.mouse.get_pressed()
        
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                return None
                
        # Check button hover and clicks
        theme1_button.check_hover(mouse_pos)
        theme2_button.check_hover(mouse_pos)
        
        if theme1_button.is_clicked(mouse_pos, mouse_click):
            selected_theme = "theme1"
            running = False
            
        if theme2_button.is_clicked(mouse_pos, mouse_click):
            selected_theme = "theme2"
            running = False
            
        # Draw screen
        screen.fill(p.Color(253,251,212))
        
        # Draw title
        font = p.font.Font("freesansbold.ttf", 36)
        title_surf = font.render("Select Chess Theme", True, p.Color("black"))
        title_rect = title_surf.get_rect(center=(BOARD_WIDTH//2, BOARD_HEIGHT//4))
        screen.blit(title_surf, title_rect)
        
        # Draw buttons
        theme1_button.draw(screen)
        theme2_button.draw(screen)
        
        rule_font = p.font.Font("freesansbold.ttf", 22)
        rules = rule_font.render("Use Z to undo and R for restart", True, p.Color("black"))
        rule_rect = rules.get_rect(center=(BOARD_WIDTH//2, 3*BOARD_HEIGHT//4))
        screen.blit(rules, rule_rect)
        p.display.flip()
        clock.tick(MAX_FPS)
        
        # Add small delay to prevent multiple clicks
        if any(mouse_click):
            p.time.delay(200)
            
    return selected_theme


#main code- user input and updating graphics
def main():
    selected_theme = theme_selection_screen()
    if selected_theme is None:
        return
        
    # Load images based on selected theme
    loadImages(THEMES[selected_theme])
    
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    moveLogFont = p.font.SysFont("Arial", 12, False, False)
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False
    animate =False
    # print(gs.board)
    gameOver=False
    playerOne = True  # If a player is playing White it's true, if AI is playing it's false
    playerTwo = False  # If a player is playing Black it's true, if AI is playing it's false
    AIThinking = False
    moveFinderProcess = None
    moveUndone = False
    #loadImages()
    sqSelected = ()       # track of last click of user (tuple: (row, col))
    playerClicks = []     # track of player clicks (two tuples)
    running = True
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos()         #coordinates of mouse click
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col) or col >= 8:
                        sqSelected = ()          
                        playerClicks = []
                    else:   
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2 and humanTurn:
                        move=ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        # print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate=True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks=[sqSelected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r:
                    # pass
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True

        # AI turn       
        if not gameOver and not humanTurn and not moveUndone:
           if not AIThinking: 
              AIThinking = True
              print("thinking...")
              returnQueue = Queue()#used to pass data between threads
              moveFinderProcess = Process(target = SmartMoveFinder.findBestMove, args = (gs,validMoves,returnQueue))
              moveFinderProcess.start() #call findBestMove(gs,validMoves, returnQueue)
              #AIMove = SmartMoveFinder.findBestMoveMinMax(gs, validMoves)
        
        # Check if AI has finished thinking
        if AIThinking and not moveFinderProcess.is_alive():
            print("done thinking")
            try:
                AIMove = returnQueue.get(timeout=1)  # Add timeout to prevent hanging
                if AIMove is None:
                    AIMove = SmartMoveFinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
            except:
                AIMove = SmartMoveFinder.findRandomMove(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
            finally:
                AIThinking = False
                moveFinderProcess.terminate()

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate=False
        drawGameState(screen,gs,validMoves, sqSelected,selected_theme)
        
        if gs.checkMate or gs.staleMate:
            gameOver = True
            text = 'stalemate' if gs.staleMate else 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate'
            drawEndGameText(screen,text)
                   
        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen,gs,validMoves, sqSelected,selected_theme):
    drawBoard(screen, sqSelected)               #draw the board
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen,gs.board)     #draw the pieces on the board
    moveLogFont = p.font.SysFont("Arial", 12, False, False)
    drawMoveLog(screen, gs, moveLogFont)     #draw the move log

def drawBoard(screen,  sqSelected):
    colors=[p.Color(240, 217, 181, 1), p.Color(181, 136, 99, 1)]       #square colors
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color=colors[((r+c)%2)]
            if (r,c) == sqSelected:
                color = p.Color(130,151,105,1)
            p.draw.rect(screen,color,p.Rect(c*SQ_SIZE,r*SQ_SIZE,SQ_SIZE,SQ_SIZE))

#Highlights square selected and moves for piece selected
def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight square selected and moves for piece selected.
    """
    if (len(game_state.moveLog)) > 0:
        last_move = game_state.moveLog[-1]
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.endCol* SQ_SIZE, last_move.endRow* SQ_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                'w' if game_state.whiteToMove else 'b'):  # square_selected is a piece that can be moved
            # highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # transparency value 0 -> transparent, 255 -> opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.startRow == row and move.startCol == col:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece!="--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))         #piece on board

'''
Draws the move log
'''

def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(BOARD_WIDTH,0,MOVE_LOG_PANEL_WIDTH,MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen,p.Color('black'),moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0,len(moveLog),2):
        moveString = str(i//2 + 1) + ". " + str(moveLog[i]) + " "
        if i + 1 < len(moveLog): #make sure black made a move5*+ Q45+
            moveString += str(moveLog[i + 1]) + " "
        moveTexts.append(moveString)
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(len(moveTexts)):
        text =  str(moveTexts[i])
        text_object = font.render(text, True, p.Color('white')) 
        text_location = moveLogRect.move(padding,textY)
        screen.blit(text_object, text_location)
        textY += text_object.get_height() + lineSpacing


def animateMove(move, screen, board, clock):
    """
    Animating a move
    """
    # global colors
    colors=[p.Color(240,217,181,1),p.Color(181,136,99,1)]
    dRow = move.endRow - move.startRow
    dCol = move.endCol - move.startCol
    frames_per_square = 10  # frames to move one square
    frame_count = (abs(dRow) + abs(dCol)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.startRow + dRow * frame / frame_count, move.startCol + dCol * frame / frame_count)
        drawBoard(screen , (row,col))
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.endRow + move.endCol) % 2]
        end_square = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enpassantRow = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                end_square = p.Rect(move.endCol * SQ_SIZE, enpassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], end_square)
        # draw moving piece
        if move.pieceMoved != '--':
            screen.blit(IMAGES[move.pieceMoved], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))

if __name__ == "__main__":
    main()