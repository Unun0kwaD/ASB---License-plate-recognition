class PiCamera():
    def __init__(self, src=0, img_size=(640,480), fps=36, rotate_180=False):
        self.img_size = img_size
        self.fps = fps
        self.cap = cv2.VideoCapture(src)
        #self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        #self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.img_size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.img_size[1])
        self.rotate_180 = rotate_180
    def run(self):       
        # read the frame
        ret, image = self.cap.read()
        if self.rotate_180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        if not ret:
            raise RuntimeError("failed to read frame")
        return image 
