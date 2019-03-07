from keras import Input, Model
from keras.layers import Conv2D, Conv1D
from keras.optimizers import SGD
from keras.utils.vis_utils import plot_model
from config import *
from layers.ConfidenceLayer import Confidence
from layers.Convert2Image import Convert2Image
from layers.GraphLSTM import GraphLSTM
from layers.GraphPropagation import GraphPropagation
from layers.InverseGraphPropagation import InverseGraphPropagation


def create_model():
    # INPUTS
    image = Input(shape=IMAGE_SHAPE, name="Image")
    slic = Input(shape=SLIC_SHAPE, name="SLIC")
    superpixels = Input(shape=(N_SUPERPIXELS, IMAGE_SHAPE[2]), name="Vertices")
    neighbors = Input(shape=(N_SUPERPIXELS, N_SUPERPIXELS), name="Neighborhood")

    # CONFIDENCE MAP
    confidence = Confidence(N_SUPERPIXELS, name="ConfidenceMap")([image, slic])

    # GRAPH PROPAGATION
    graph, reverse = GraphPropagation(N_SUPERPIXELS, name="GraphPath")([superpixels, confidence, neighbors])

    # MAIN LSTM PART
    lstm = GraphLSTM(IMAGE_SHAPE[-1], return_sequences=True, name="G-LSTM")(graph)

    # INVERSE GRAPH PROPAGATION
    out_vertices = InverseGraphPropagation(name="InvGraphPath")([lstm, reverse])

    out = Conv1D(IMAGE_SHAPE[-1], 1, name="OutputConv")(out_vertices)

    # # TO IMAGE CONVERSION
    # to_image = Convert2Image(max_segments=N_SUPERPIXELS, name="ToImage")([out_vertices, slic])
    # # OUTPUT
    # output = Conv2D(IMAGE_SHAPE[-1], kernel_size=1, padding="same", name="OutputConvolution")(to_image)
    # model = Model(inputs=[image,
    #                       slic,
    #                       superpixels,
    #                       neighbors],
    #               outputs=[output])

    model = Model(inputs=[image,
                          slic,
                          superpixels,
                          neighbors],
                  outputs=[out])

    model.summary()

    # PLOT
    # plot_model(model, show_shapes=True)

    # OPTIMIZER
    sgd = SGD(momentum=0.9, decay=0.0005)
    model.compile(sgd, loss="mse", metrics=["acc"])
    model.save(MODEL_PATH)


if __name__ == '__main__':
    create_model()
