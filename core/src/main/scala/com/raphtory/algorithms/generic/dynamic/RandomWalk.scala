package com.raphtory.algorithms.generic.dynamic

import com.raphtory.algorithms.generic.dynamic.RandomWalk.Message
import com.raphtory.algorithms.generic.dynamic.RandomWalk.WalkMessage
import com.raphtory.algorithms.generic.dynamic.RandomWalk.StoreMessage
import com.raphtory.algorithms.api._
import com.raphtory.algorithms.api.GraphAlgorithm
import com.raphtory.algorithms.api.GraphPerspective
import com.raphtory.algorithms.api.Table
import com.raphtory.graph.visitor.Vertex

import collection.mutable.ArrayBuffer
import scala.util.Random

/**
  * {s}`RandomWalk(walkLength: Int = 10, numWalks: Int = 1, seed: Long = -1)`
  *    : Implements random walks on unweighted graph
  *
  *  This algorithm starts `numWalks` unbiased random walks from each node
  *  and terminates them after the walks have reached `walkLength` nodes. The network is treated as directed and if a
  *  vertex has no outgoing edges, the walk remains at this vertex for the remaining steps.
  *
  * ## Parameters
  *
  *  {s}`walkLength: Int = 10`
  *    : maximum length of generated walks
  *
  *  {s}`numWalks: Int = 1`
  *    : number of walks to start for each node
  *
  *  {s}`seed: Long`
  *    : seed for the random number generator
  *
  * ```{note}
  * Currently, results are non-deterministic even with fixed seed, likely due to non-deterministic message order.
  * ```
  *
  * ## States
  *
  *  {s}`walks: Array[ArrayBuffer[String]]`: List of nodes for each random walk started from this vertex
  *
  * ## Returns
  *
  * | vertex 1          | vertex 2          | ... | vertex `walkLength` |
  * | ----------------- | ----------------- | --- | ------------------- |
  * | {s}`name: String` | {s}`name: String` | ... | {s}`name: String`   |
  *
  *  Each row of the table corresponds to a single random walk and columns correspond to the vertex at a given step
  */
class RandomWalk(walkLength: Int, numWalks: Int, seed: Long = -1) extends GraphAlgorithm {
  protected val rnd: Random = if (seed != -1) new Random(seed) else new Random()

  protected def selectNeighbour(vertex: Vertex): Long = {
    val neighbours = vertex.getOutNeighbours()
    if (neighbours.isEmpty)
      vertex.ID()
    else
      neighbours(rnd.nextInt(neighbours.length))
  }

  override def apply(graph: GraphPerspective): GraphPerspective =
    graph
      .step { vertex =>
        val walks = Array.fill(numWalks)(ArrayBuffer.empty[String])
        vertex.setState("walks", walks)
        for (walkID <- 0 until numWalks)
//          initialise walks
          vertex.messageSelf(WalkMessage(vertex.ID(), walkID))
      }
      .iterate(
              vertex =>
                vertex.messageQueue[Message].foreach {
//              propagate walks
                  case WalkMessage(source, walkID) =>
                    vertex.messageVertex(source, StoreMessage(vertex.name(), walkID))
                    vertex.messageVertex(selectNeighbour(vertex), WalkMessage(source, walkID))
                  //          store walks on source node
                  case StoreMessage(name, walkID)  =>
                    val walks = vertex.getState[Array[ArrayBuffer[String]]]("walks")
                    walks(walkID).append(name)
                },
              walkLength,
              executeMessagedOnly = true
      )
      .step { vertex =>
//      collect last step of walk
        vertex.messageQueue[Message].foreach {
          case WalkMessage(source, walkID) =>
          case StoreMessage(name, walkID)  =>
            val walks = vertex.getState[Array[ArrayBuffer[String]]]("walks")
            walks(walkID).append(name)
        }
      }

  override def tabularise(graph: GraphPerspective): Table =
    graph
      .select(vertex => Row(vertex.getState[Array[ArrayBuffer[String]]]("walks")))
      .explode(row => row.getAs[Array[ArrayBuffer[String]]](0).map(r => Row(r.toSeq: _*)).toList)
}

object RandomWalk {

  def apply(walkLength: Int = 10, numWalks: Int = 1, seed: Long = -1) =
    new RandomWalk(walkLength, numWalks, seed)

  sealed abstract class Message
  case class WalkMessage(sourceID: Long, walkID: Int) extends Message
  case class StoreMessage(name: String, walkID: Int)  extends Message
}