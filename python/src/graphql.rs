use pyo3::{exceptions, exceptions::PyException, prelude::*};
use pyo3_asyncio::tokio;
use raphtory_core::{
    db::api::view::MaterializedGraph,
    python::{
        packages::vectors::{spawn_async_task, PyDocumentTemplate},
        utils::errors::adapt_err_value,
    },
    vectors::embeddings::openai_embedding,
};
use raphtory_graphql::{url_decode_graph, url_encode_graph, RaphtoryServer};
use std::{collections::HashMap, future::Future, path::PathBuf, thread};

#[pyfunction]
pub fn from_map(
    py: Python,
    graphs: HashMap<String, MaterializedGraph>,
    port: Option<u16>,
) -> PyResult<&PyAny> {
    let server = RaphtoryServer::from_map(graphs);
    let port = port.unwrap_or(1736);
    pyo3_asyncio::tokio::future_into_py(py, async move {
        server
            .run_with_port(port)
            .await
            .map_err(|e| adapt_err_value(&e))
    })
}

#[pyfunction]
pub fn from_directory(
    py: Python,
    path: String,
    port: Option<u16>,
    vectorise: Option<String>,
    cache: Option<String>,
) -> PyResult<&PyAny> {
    let server = RaphtoryServer::from_directory(path.as_str());
    let port = port.unwrap_or(1736);

    let vector_server = match (vectorise, cache) {
        (Some(vectorise), Some(cache)) => {
            let cache = PathBuf::from(cache);
            let template = Some(PyDocumentTemplate::new(
                Some("document".to_owned()),
                Some("document".to_owned()),
            ));
            spawn_async_task(move || async move {
                server
                    .with_vectorised(vec![vectorise], openai_embedding, &cache, template)
                    .await
            })
        }
        (None, None) => server,
        _ => Err(PyException::new_err(
            "invalid arguments, you have to set both vectorise and cache accordingly",
        ))?,
    };

    tokio::future_into_py(py, async move {
        vector_server
            .run_with_port(port)
            .await
            .map_err(|e| adapt_err_value(&e))
    })
}

#[pyfunction]
pub fn from_map_and_directory(
    py: Python,
    graphs: HashMap<String, MaterializedGraph>,
    path: String,
    port: Option<u16>,
) -> PyResult<&PyAny> {
    let port = port.unwrap_or(1736);
    let server = RaphtoryServer::from_map_and_directory(graphs, path.as_str());
    pyo3_asyncio::tokio::future_into_py(py, async move {
        server
            .run_with_port(port)
            .await
            .map_err(|e| adapt_err_value(&e))
    })
}

#[pyfunction]
pub fn encode_graph(graph: MaterializedGraph) -> PyResult<String> {
    let result = url_encode_graph(graph);
    match result {
        Ok(s) => Ok(s),
        Err(e) => Err(exceptions::PyValueError::new_err(format!(
            "Error encoding: {:?}",
            e
        ))),
    }
}

#[pyfunction]
pub fn decode_graph(py: Python, encoded_graph: String) -> PyResult<PyObject> {
    let result = url_decode_graph(encoded_graph);
    match result {
        Ok(s) => Ok(s.into_py(py)),
        Err(e) => Err(exceptions::PyValueError::new_err(format!(
            "Error decoding: {:?}",
            e
        ))),
    }
}
