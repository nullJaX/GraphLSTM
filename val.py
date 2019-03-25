import numpy
from keras.engine.saving import load_model
from skimage import io
from skimage.transform import resize
from tqdm import tqdm

from config import MODEL_PATH, VALSET_FILE, IMAGES_PATH, N_SUPERPIXELS, \
    SLIC_SIGMA, OUTPUT_PATH, IMAGE_SHAPE, VALIDATION_IMAGES
from layers.ConfidenceLayer import Confidence
from layers.GraphLSTM import GraphLSTM
from layers.GraphLSTMCell import GraphLSTMCell
from layers.GraphPropagation import GraphPropagation
from layers.InverseGraphPropagation import InverseGraphPropagation
from utils.utils import obtain_superpixels, average_rgb_for_superpixels, \
    get_neighbors

if __name__ == '__main__':
    with open(VALSET_FILE) as f:
        image_list = [line.replace("\n", "") for line in f]

    model = load_model(MODEL_PATH, custom_objects={'Confidence': Confidence,
                                                   'GraphPropagation': GraphPropagation,
                                                   'InverseGraphPropagation': InverseGraphPropagation,
                                                   'GraphLSTM': GraphLSTM,
                                                   'GraphLSTMCell': GraphLSTMCell})

    for image_name in tqdm(image_list):
        image = io.imread(IMAGES_PATH + image_name + ".jpg")
        shape = image.shape
        img = resize(image, IMAGE_SHAPE, anti_aliasing=True)
        slic = obtain_superpixels(img, N_SUPERPIXELS, SLIC_SIGMA)
        vertices = average_rgb_for_superpixels(img, slic)
        neighbors = get_neighbors(slic, N_SUPERPIXELS)

        # TO NUMPIES
        img = numpy.expand_dims(numpy.array(img), axis=0)
        slic = numpy.expand_dims(numpy.array(slic), axis=0)
        vertices = numpy.expand_dims(numpy.array(vertices), axis=0)
        neighbors = numpy.expand_dims(numpy.array(neighbors), axis=0)

        output_vertices, _ = model.predict_on_batch([img, slic, vertices, neighbors])

        slic_out = slic
        output_image = numpy.zeros(img[0].shape, dtype="uint8")
        for segment_num in range(output_vertices.shape[1]):
            if segment_num not in numpy.unique(slic):
                break
            mask = numpy.zeros(slic[0, :, :].shape + (3,), dtype="uint8")
            mask[slic[0, :, :] == segment_num] = 255 * output_vertices[0, segment_num, :]
            output_image += mask

        output_image = resize(output_image, shape, anti_aliasing=True)
        output_image = numpy.clip(output_image * 255, 0, 255)
        expected_image = io.imread(VALIDATION_IMAGES + image_name + ".png")
        i = numpy.concatenate((image, expected_image, output_image), axis=1)
        output = numpy.clip(i, 0, 255)
        output = output.astype(numpy.uint8)
        io.imsave(OUTPUT_PATH + image_name + ".png", output)
