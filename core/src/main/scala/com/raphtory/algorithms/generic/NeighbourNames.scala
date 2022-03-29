package com.raphtory.algorithms.generic

import com.raphtory.algorithms.api.GraphAlgorithm
import com.raphtory.algorithms.api.GraphPerspective

/**
  * {s}`NeighbourNames()`
  *  : Get name of all neighbours and store the map from vertexID to name in state "neighbourNames".
  *
  *  This is mainly useful as part of algorithms or chains that return neighbourhood or edge information.
  *
  * ## States
  *
  *  {s}`neighbourNames: Map[Long, String]`
  *    : map of vertex ID to name for all neighbours of vertex
  *
  * ## Returns
  *
  *  This algorithm does not return anything.
  *
  *  ```{seealso}
  *  [](com.raphtory.algorithms.generic.EdgeList)
  *  [](com.raphtory.algorithms.temporal.TemporalEdgeList)
  *  ```
  */
class NeighbourNames extends GraphAlgorithm {

  override def apply(graph: GraphPerspective): GraphPerspective =
    graph
      .step(vertex => vertex.messageAllNeighbours((vertex.ID(), vertex.name())))
      .step { vertex =>
        vertex.setState("neighbourNames", vertex.messageQueue[(Long, String)].toMap)
      }
}

object NeighbourNames {
  def apply() = new NeighbourNames
}