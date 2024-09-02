###############################################################################
#                                                                             #
#                      AUTOGENERATED TYPE STUB FILE                           #
#                                                                             #
#    This file was automatically generated. Do not modify it directly.        #
#    Any changes made here may be lost when the file is regenerated.          #
#                                                                             #
###############################################################################

class GraphServer:
    """A class for defining and running a Raphtory GraphQL server"""

    def __init__(
        self,
        work_dir,
        cache_capacity=None,
        cache_tti_seconds=None,
        log_level=None,
        config_path=None,
    ):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def run(self, port=1736, timeout_ms=...):
        """
        Run the server until completion.

        Arguments:
          port (int): The port to use (defaults to 1736).
        """

    def start(self, port=1736, timeout_ms=None):
        """
        Start the server and return a handle to it.

        Arguments:
          port (int):  the port to use (defaults to 1736).
          timeout_ms (int): wait for server to be online (defaults to 5000). The server is stopped if not online within timeout_ms but manages to come online as soon as timeout_ms finishes!
        """

    def with_document_search_function(self, name, input, function):
        """
        Register a function in the GraphQL schema for document search over a graph.

        The function needs to take a `VectorisedGraph` as the first argument followed by a
        pre-defined set of keyword arguments. Supported types are `str`, `int`, and `float`.
        They have to be specified using the `input` parameter as a dict where the keys are the
        names of the parameters and the values are the types, expressed as strings.

        Arguments:
          name (str): The name of the function in the GraphQL schema.
          input (dict): The keyword arguments expected by the function.
          function (Function): the function to run.

        Returns:
           GraphServer: A new server object containing the vectorised graphs.
        """

    def with_global_search_function(self, name, input, function):
        """
        Register a function in the GraphQL schema for document search among all the graphs.

        The function needs to take a `GraphqlGraphs` object as the first argument followed by a
        pre-defined set of keyword arguments. Supported types are `str`, `int`, and `float`.
        They have to be specified using the `input` parameter as a dict where the keys are the
        names of the parameters and the values are the types, expressed as strings.

        Arguments:
          name (str): the name of the function in the GraphQL schema.
          input (dict):  the keyword arguments expected by the function.
          function (Function): the function to run.

        Returns:
           GraphServer: A new server object containing the vectorised graphs.
        """

    def with_vectorised(
        self,
        cache,
        graph_names=None,
        embedding=None,
        graph_document=None,
        node_document=None,
        edge_document=None,
    ):
        """
        Vectorise a subset of the graphs of the server.

        Note:
          If no embedding function is provided, the server will attempt to use the OpenAI API
          embedding model, which will only work if the env variable OPENAI_API_KEY is set
          appropriately

        Arguments:
          graph_names (List[str]): the names of the graphs to vectorise. All by default.
          cache (str):  the directory to use as cache for the embeddings.
          embedding (Function):  the embedding function to translate documents to embeddings.
          graph_document (String):  the property name to use as the source for the documents on graphs.
          node_document (String):  the property name to use as the source for the documents on nodes.
          edge_document (String):  the property name to use as the source for the documents on edges.

        Returns:
           GraphServer: A new server object containing the vectorised graphs.
        """

class GraphqlGraphs:
    """
    A class for accessing graphs hosted in a Raphtory GraphQL server and running global search for
    graph documents
    """

    def __init__(self):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def get(self, name):
        """Return the `VectorisedGraph` with name `name` or `None` if it doesn't exist"""

    def search_graph_documents(self, query, limit, window):
        """
        Return the top documents with the smallest cosine distance to `query`

        # Arguments
          * query - the text or the embedding to score against
          * limit - the maximum number of documents to return
          * window - the window where documents need to belong to in order to be considered

        # Returns
          A list of documents
        """

    def search_graph_documents_with_scores(self, query, limit, window):
        """Same as `search_graph_documents` but it also returns the scores alongside the documents"""

class RaphtoryClient:
    """A client for handling GraphQL operations in the context of Raphtory."""

    def __init__(self, url):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def copy_graph(self, path, new_path):
        """
        Copy graph from a path `path` on the server to a `new_path` on the server

        Arguments:
          * `path`: the path of the graph to be copied
          * `new_path`: the new path of the copied graph

        Returns:
           Copy status as boolean
        """

    def delete_graph(self, path):
        """
        Delete graph from a path `path` on the server

        Arguments:
          * `path`: the path of the graph to be deleted

        Returns:
           Delete status as boolean
        """

    def is_server_online(self):
        """
        Check if the server is online.

        Returns:
           Returns true if server is online otherwise false.
        """

    def move_graph(self, path, new_path):
        """
        Move graph from a path `path` on the server to a `new_path` on the server

        Arguments:
          * `path`: the path of the graph to be moved
          * `new_path`: the new path of the moved graph

        Returns:
           Move status as boolean
        """

    def new_graph(self, path, graph_type):
        """
        Create a new Graph on the server at `path`

        Arguments:
          * `path`: the path of the graph to be created
          * `graph_type`: the type of graph that should be created - this can be EVENT or PERSISTENT

        Returns:
           None

        """

    def query(self, query, variables=None):
        """
        Make a graphQL query against the server.

        Arguments:
          * `query`: the query to make.
          * `variables`: a dict of variables present on the query and their values.

        Returns:
           The `data` field from the graphQL response.
        """

    def receive_graph(self, path):
        """
        Receive graph from a path `path` on the server

        Arguments:
          * `path`: the path of the graph to be received

        Returns:
           Graph as string
        """

    def remote_graph(self, path):
        """
        Get a RemoteGraph reference to a graph on the server at `path`

        Arguments:
          * `path`: the path of the graph to be created

        Returns:
           RemoteGraph

        """

    def send_graph(self, path, graph, overwrite=False):
        """
        Send a graph to the server

        Arguments:
          * `path`: the path of the graph
          * `graph`: the graph to send
          * `overwrite`: overwrite existing graph (defaults to False)

        Returns:
           The `data` field from the graphQL response after executing the mutation.
        """

    def upload_graph(self, path, file_path, overwrite=False):
        """
        Upload graph file from a path `file_path` on the client

        Arguments:
          * `path`: the name of the graph
          * `file_path`: the path of the graph on the client
          * `overwrite`: overwrite existing graph (defaults to False)

        Returns:
           The `data` field from the graphQL response after executing the mutation.
        """

class RemoteEdge:
    def __init__(self, path, client, src, dst):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def add_constant_properties(self, properties, layer=None):
        """
        Add constant properties to the edge within the remote graph.
        This function is used to add properties to an edge that remain constant and do not
        change over time. These properties are fundamental attributes of the edge.

        Parameters:
            properties (Dict[str, Prop]): A dictionary of properties to be added to the edge.
            layer (str): The layer you want these properties to be added on to.
        """

    def add_updates(self, t, properties=None, layer=None):
        """
        Add updates to an edge in the remote graph at a specified time.
        This function allows for the addition of property updates to an edge within the graph. The updates are time-stamped, meaning they are applied at the specified time.

        Parameters:
            t (int | str | DateTime): The timestamp at which the updates should be applied.
            properties (Optional[Dict[str, Prop]]): A dictionary of properties to update.
            layer (str): The layer you want the updates to be applied.
        """

    def delete(self, t, layer=None):
        """
        Mark the edge as deleted at the specified time.

        Parameters:
            t (int | str | DateTime): The timestamp at which the deletion should be applied.
            layer (str): The layer you want the deletion applied to.
        """

    def update_constant_properties(self, properties, layer=None):
        """
        Update constant properties of an edge in the remote graph overwriting existing values.
        This function is used to add properties to an edge that remains constant and does not
        change over time. These properties are fundamental attributes of the edge.

        Parameters:
            properties (Dict[str, Prop]): A dictionary of properties to be added to the edge.
            layer (str): The layer you want these properties to be added on to.
        """

class RemoteEdgeAddition:
    def __init__(self, src, dst, layer=None, constant_properties=None, updates=None):
        """Initialize self.  See help(type(self)) for accurate signature."""

class RemoteGraph:
    def __init__(self, path, client):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def add_constant_properties(self, properties):
        """
        Adds constant properties to the remote graph.

        Arguments:
            properties (dict): The constant properties of the graph.
        """

    def add_edge(self, timestamp, src, dst, properties=None, layer=None):
        """
        Adds a new edge with the given source and destination nodes and properties to the remote graph.

        Arguments:
           timestamp (int|str|Datetime): The timestamp of the edge.
           src (str|int): The id of the source node.
           dst (str|int): The id of the destination node.
           properties (dict): The properties of the edge, as a dict of string and properties (optional).
           layer (str): The layer of the edge (optional).

        Returns:
          RemoteEdge
        """

    def add_edges(self, updates):
        """
        Batch add edge updates to the remote graph

        Arguments:
          updates (List[RemoteEdgeAddition]): The list of updates you want to apply to the remote graph
        """

    def add_node(self, timestamp, id, properties=None, node_type=None):
        """
        Adds a new node with the given id and properties to the remote graph.

        Arguments:
           timestamp (int|str|Datetime): The timestamp of the node.
           id (str|int): The id of the node.
           properties (dict): The properties of the node (optional).
           node_type (str): The optional string which will be used as a node type
        Returns:
          RemoteNode
        """

    def add_nodes(self, updates):
        """
        Batch add node updates to the remote graph

        Arguments:
          updates (List[RemoteNodeAddition]): The list of updates you want to apply to the remote graph
        """

    def add_property(self, timestamp, properties):
        """
        Adds properties to the remote graph.

        Arguments:
           timestamp (int|str|Datetime): The timestamp of the temporal property.
           properties (dict): The temporal properties of the graph.
        """

    def delete_edge(self, timestamp, src, dst, layer=None):
        """
        Deletes an edge in the remote graph, given the timestamp, src and dst nodes and layer (optional)

        Arguments:
          timestamp (int): The timestamp of the edge.
          src (str|int): The id of the source node.
          dst (str|int): The id of the destination node.
          layer (str): The layer of the edge. (optional)

        Returns:
          RemoteEdge
        """

    def edge(self, src, dst):
        """
        Gets a remote edge with the specified source and destination nodes

        Arguments:
            src (str|int): the source node id
            dst (str|int): the destination node id

        Returns:
            RemoteEdge
        """

    def node(self, id):
        """
        Gets a remote node with the specified id

        Arguments:
          id (str|int): the node id

        Returns:
          RemoteNode
        """

    def update_constant_properties(self, properties):
        """
        Updates constant properties on the remote graph.

        Arguments:
            properties (dict): The constant properties of the graph.
        """

class RemoteNode:
    def __init__(self, path, client, id):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def add_constant_properties(self, properties):
        """
        Add constant properties to a node in the remote graph.
        This function is used to add properties to a node that remain constant and does not
        change over time. These properties are fundamental attributes of the node.

        Parameters:
            properties (Dict[str, Prop]): A dictionary of properties to be added to the node.
        """

    def add_updates(self, t, properties=None):
        """
        Add updates to a node in the remote graph at a specified time.
        This function allows for the addition of property updates to a node within the graph. The updates are time-stamped, meaning they are applied at the specified time.

        Parameters:
            t (int | str | DateTime): The timestamp at which the updates should be applied.
            properties (Dict[str, Prop]): A dictionary of properties to update.
        """

    def set_node_type(self, new_type):
        """
        Set the type on the node. This only works if the type has not been previously set, otherwise will
        throw an error

        Parameters:
            new_type (str): The new type to be set

        Returns:
            Result: A result object indicating success or failure.
        """

    def update_constant_properties(self, properties):
        """
        Update constant properties of a node in the remote graph overwriting existing values.
        This function is used to add properties to a node that remain constant and do not
        change over time. These properties are fundamental attributes of the node.

        Parameters:
            properties (Dict[str, Prop]): A dictionary of properties to be added to the node.
        """

class RemoteNodeAddition:
    def __init__(self, name, node_type=None, constant_properties=None, updates=None):
        """Initialize self.  See help(type(self)) for accurate signature."""

class RemoteUpdate:
    def __init__(self, time, properties=None):
        """Initialize self.  See help(type(self)) for accurate signature."""

class RunningGraphServer:
    """A Raphtory server handler that also enables querying the server"""

    def __init__(self):
        """Initialize self.  See help(type(self)) for accurate signature."""

    def get_client(self): ...
    def stop(self):
        """Stop the server and wait for it to finish"""
