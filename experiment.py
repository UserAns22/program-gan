import tensorflow as tf
import string as sn
import numpy as np

# The location on the disk of project
PROJECT_BASEDIR = ("C:/Users/brand/Google Drive/" +
    "Academic/Research/Program Synthesis with Deep Learning/Repo/program-gan/")


# The location on the disk of checkpoints
CHECKPOINT_BASEDIR = (PROJECT_BASEDIR + "Checkpoints/")


# The location on the disk of project
DATASET_BASEDIR = ("C:/Users/brand/Google Drive/" +
    "Academic/Research/Program Synthesis with Deep Learning/Datasets/")


# Filenames associated with program dataset
DATASET_FILENAMES_PYTHON = [
    (DATASET_BASEDIR + "epf_8_dataset.csv")
]


# Locate dataset files on hard disk
for FILE_PYTHON in DATASET_FILENAMES_PYTHON:
    if not tf.gfile.Exists(FILE_PYTHON):
        raise ValueError('Failed to find file: ' + FILE_PYTHON)


# Dataset configuration constants
DATASET_IO_EXAMPLES = 10
DATASET_COLUMNS = (DATASET_IO_EXAMPLES * 2) + 2
DATASET_DEFAULT = "0"


# Tokenization parameters for python
DATASET_VOCABULARY = sn.printable
DATASET_MAXIMUM = 64


# Convert elements of python source code to one-hot token vectors
def tokenize_source_code_python(source_code_python, vocabulary=DATASET_VOCABULARY):
    
    # List allowed characters
    mapping_characters = tf.string_split([vocabulary], delimiter="")


    # List characters in each word
    input_characters = tf.string_split([source_code_python], delimiter="")


    # Convert integer lookup table
    lookup_table = tf.contrib.lookup.index_table_from_tensor(mapping=mapping_characters.values, default_value=0)


    # Query lookup table
    one_hot_tensor = tf.one_hot(lookup_table.lookup(input_characters.values), len(vocabulary), dtype=tf.float32)


    # Calculate actual sequence length
    actual_length = tf.size(one_hot_tensor) // len(vocabulary)


    # Pad input to match DATASET_MAXIMUM
    expanded_tensor = tf.pad(one_hot_tensor, [[0, (DATASET_MAXIMUM - actual_length)], [0, 0]])

    return tf.reshape(expanded_tensor, [DATASET_MAXIMUM, len(vocabulary)]), actual_length


# Read single row words
def decode_record_python(filename_queue, num_columns=DATASET_COLUMNS, default_value=DATASET_DEFAULT):

    # Attach text file reader
    DATASET_READER = tf.TextLineReader(skip_header_lines=1)


    # Read single line from dataset
    key, value_text = DATASET_READER.read(filename_queue)


    # Decode line to columns of strings
    name_column, *example_columns, function_column = tf.decode_csv(value_text, [[default_value] for i in range(num_columns)])


    # Convert IO examples from string to float32
    example_columns = tf.string_to_number(tf.stack(example_columns), out_type=tf.float32)


    # Convert python code to tokenized one-hot vectors
    program_tensor, actual_length = tokenize_source_code_python(function_column)

    return name_column, example_columns, program_tensor, actual_length


# Batch configuration constants
BATCH_SIZE = 32
NUM_THREADS = 4
TOTAL_EXAMPLES = 2015538


# Generate batch from rows
def generate_batch(name, examples, program, length, batch_size=BATCH_SIZE, num_threads=NUM_THREADS, shuffle_batch=True):

    # Shuffle batch randomly
    if shuffle_batch:

        # Construct batch from queue of records
        name_batch, examples_batch, program_batch, length_batch = tf.train.shuffle_batch(
            [name, examples, program, length],
            batch_size=batch_size,
            num_threads=num_threads,
            capacity=TOTAL_EXAMPLES,
            min_after_dequeue=(TOTAL_EXAMPLES // 1000))


    # Preserve order of batch
    else:

        # Construct batch from queue of records
        name_batch, examples_batch, program_batch, length_batch = tf.train.batch(
            [name, examples, program, length],
            batch_size=batch_size,
            num_threads=num_threads,
            capacity=TOTAL_EXAMPLES)

    return name_batch, examples_batch, program_batch, length_batch



# Generate single training batch of python programs
def training_batch_python():

    # A queue to generate batches
    filename_queue = tf.train.string_input_producer(DATASET_FILENAMES_PYTHON)


    # Decode from string to floating point
    name, examples, program, length = decode_record_python(filename_queue)


    # Combine example queue into batch
    name_batch, examples_batch, program_batch, length_batch = generate_batch(name, examples, program, length)

    return name_batch, examples_batch, program_batch, length_batch


# Prefix model nomenclature
PREFIX_RNN = "rnn"
PREFIX_DENSE = "dense"
PREFIX_SOFTMAX = "softmax"
PREFIX_TOTAL = "total"


# Extension model nomenclature
EXTENSION_NUMBER = (lambda number: "_" + str(number))
EXTENSION_LOSS = "_loss"
EXTENSION_WEIGHTS = "_weights"
EXTENSION_BIASES = "_biases"
EXTENSION_OFFSET = "_offset"
EXTENSION_SCALE = "_scale"
EXTENSION_ACTIVATION = "_activation"
EXTENSION_COLUMN = "_column"


# Collection model nomenclature
COLLECTION_LOSSES = "losses"
COLLECTION_PARAMETERS = "parameters"
COLLECTION_ACTIVATIONS = "activations"


# Initialize trainable parameters
def initialize_weights_cpu(name, shape, standard_deviation=0.01, decay_factor=None):

    # Force usage of cpu
    with tf.device("/cpu:0"):

        # Sample weights from normal distribution
        weights = tf.get_variable(
            name,
            shape, 
            initializer=tf.truncated_normal_initializer(
                stddev=standard_deviation,
                dtype=tf.float32),
            dtype=tf.float32)

    # Add weight decay to loss function
    if decay_factor is not None:

        # Calculate decay with l2 loss
        weight_decay = tf.multiply(
            tf.nn.l2_loss(weights), 
            decay_factor, 
            name=(name + EXTENSION_LOSS))
        tf.add_to_collection(COLLECTION_LOSSES, weight_decay)

    return weights


# Initialize trainable parameters
def initialize_biases_cpu(name, shape):

    # Force usage of cpu
    with tf.device("/cpu:0"):

        # Sample weights from normal distribution
        biases = tf.get_variable(
            name,
            shape, 
            initializer=tf.constant_initializer(1.0),
            dtype=tf.float32)

    return biases


# Compute corrected tokenized code with rnn
def inference_generator_python(program_batch):

    return program_batch


# Compute behavior function with rnn
def inference_behavior_python(program_batch):

    # Compute expected output given input example
    def behavior_function(input_example):

        return input_example

    return behavior_function


# Non-destructively creates a mutated program batch
# Runtime is O(BATCH_SIZE * DATASET_MAXIMUM)
def get_mutated_batch(program_batch):

    # Froce usage of cpu
    with tf.device("/cpu:0"):

        no_of_mutations = tf.placeholder(tf.int32, shape=(1), name="number of mutations in program")

        vocab_size = len(DATASET_VOCABULARY)

        # initialize the mutated batch
        mutated_batch = tf.zeros(program_batch.get_shape())

        for i in range(len(mutated_batch)):

            program = mutated_batch[i]
            original_program = program_batch[i]

            random_mutation_indices = tf.zeros([DATASET_MAXIMUM])  # weird implementation to optimize runtime from O(DATASET_MAXIMUM^2) to O(DATASET_MAXIMUM)
            no_of_indices_set = 0

            while no_of_indices_set < no_of_mutations:

                # index of a random character to be mutated
                random_index = np.random_integer(0, high=DATASET_MAXIMUM - 1)

                # making sure we are not mutating the same spot again
                if random_mutation_indices[random_index] != 1:
                    random_mutation_indices[random_index] = 1
                    no_of_indices_set += 1

            for j in range(len(program)):

                # if character at this index is to be mutated, create new random one-hot vec and copy to program
                if random_mutation_indices[j] == 1:
                    program[j] = tf.one_hot([np.random_integer(0, high=vocab_size - 1)], vocab_size, dtype=tf.float32)
                else:
                    program[j] = original_program[j]  # copy one-hot vec from origin program to new program

    return mutated_batch


# Compute syntax label with rnn
def inference_syntax_python(program_batch):

    # program_batch shape = [batch_size, DATASET_MAXIMUM (max num_steps), len(vocabulary)]
    # lstm_size should be length of the one-hot vec = len(vocabulary)
    # state = tensor with shape [batch_size, state_size]

    return tf.constant([1.], dtype=tf.float32)


# Create new graph
with tf.Graph().as_default():

    # Compute single training batch
    name_batch, examples_batch, program_batch, length_batch = training_batch_python()


    # Compute corrected code
    corrected_batch = inference_generator_python(program_batch)

    
    # Compute syntax of corrected code
    syntax_batch = inference_syntax_python(corrected_batch)


    # Compute behavior of corrected code
    behavior_batch = inference_behavior_python(corrected_batch)


    # Perform computation cycle based on graph
    with tf.train.MonitoredTrainingSession() as session:

        # Calculate corrected batch source code
        output = session.run(program_batch)
        print(output)