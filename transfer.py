##Imports##
import net
import utilities as utils
import tensorflow as tf
from functools import reduce
###########################

##Global Options##
contentPath        = '/Users/matthewsokoloff/Downloads/photo.jpg'
stylePath          = '/Users/matthewsokoloff/Downloads/art.jpg'
contentLayer       = 'conv4_2'
styleLayers        = ['conv1_1','conv2_1','conv3_1', 'conv4_1', 'conv5_1']
styleWeights       = [0.2      ,0.2      , 0.2     , 0.2      , 0.2      ]
styleData          = {}
contentData        = None
errorMetricContent = utils.mse #utils.euclidean
errorMetricStyle   = utils.mse #utils.euclidean
normalizeContent   = True #Inversion paper says to use this
normalizeStyle     = False #No mention of style in inversion paper
imageShape         = (224,224,3)
#TODO : Add a real value for sigma. Should be the average euclidean norm of the vgg training images. This also requires an option for the model to change whether or not sigma is multipled by the input image
sigma = 1
Beta = 2
Alpha = 6
a = 0.01
B = 128 #Pixel min/max encourages pixels to be in the range of [-B, +B]
sess = tf.Session()

##################


with tf.Session() as sess:
    inputTensor = tf.placeholder(tf.float32, shape=[None, imageShape[0], imageShape[1], imageShape[2]])
    contentImage = utils.loadImage(contentPath)
    styleImage = utils.loadImage(stylePath)
    model =net.Vgg19()
    model.build(inputTensor)
    contentData = eval('sess.run(model.' + contentLayer + ',feed_dict={inputTensor:contentImage})')
    for styleLayer in styleLayers:
        styleData[styleLayer] = eval('sess.run(model.' + styleLayer + ',feed_dict={inputTensor:styleImage})')



def buildStyleLoss():
    totalStyleLoss = []
    for index, styleLayer in enumerate(styleLayers):
        normalizingConstant = 1
        if (normalizeStyle):
            normalizingConstant = (reduce(lambda x, y: x + y, (styleData[styleLayer] ** 2)) ** (0.5))


        correctGrams = buildGramMatrix(styleData[styleLayer])
        tensorGrams  = buildGramMatrix(eval('model.'+styleLayer))
        _, dimX, dimY, num_filters = tensorGrams.get_shape()
        denominator  =(2*normalizingConstant)*((dimX*dimY)**2)*(num_filters**2)
        error        = tf.reduce_sum(errorMetricStyle(tensorGrams, correctGrams))
        totalStyleLoss.append((error/denominator))

    return (reduce(lambda x,y: x+y,totalStyleLoss))


def buildGramMatrix(layer):
    _, dimX, dimY, num_filters = layer.get_shape()
    vectorized_maps = tf.reshape(layer, [dimX * dimY, num_filters])

    if dimX * dimY > num_filters:
        return tf.matmul(vectorized_maps, vectorized_maps, transpose_a=True)
    else:
        return tf.matmul(vectorized_maps, vectorized_maps, transpose_b=True)


def buildContentLoss(correctAnswer=contentData):
    normalizingConstant = 1
    if(normalizeContent):
        normalizingConstant = (reduce(lambda x,y: x+y,(correctAnswer**2))**(0.5))

    return (eval('errorMetricContent(model.'+contentLayer+', correctAnswer)')/normalizingConstant)


#def buildAlphaNorm():
#TODO:Build alpha norm function

def buildTVNorm(inputNoiseImageVar):
    #TODO: Implement shiftDown and shiftRight
    yPlusOne = tf.shiftDown(inputNoiseImageVar)
    xPlusOne = tf.shiftRight(inputNoiseImageVar)

    lambdaBeta = (sigma**Beta) / (imageShape[0]*imageShape[1]*((a*B)**Beta))
    return lambdaBeta*tf.reduce_sum( tf.pow((tf.square(yPlusOne-inputNoiseImageVar)+tf.square(xPlusOne-inputNoiseImageVar)),(Beta/2) ))




model = net.Vgg19()
inputVar = tf.Variable(utils.createNoiseImage(imageShape))
model.build()

# Example : buildTVNorm(inputVar)

#def totalLoss():