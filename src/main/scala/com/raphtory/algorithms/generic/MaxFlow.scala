package com.raphtory.algorithms.generic

import com.raphtory.core.algorithm.GraphAlgorithm
import com.raphtory.core.algorithm.GraphPerspective
import com.raphtory.core.algorithm.Row
import com.raphtory.core.algorithm.Table

import collection.mutable
import math.Numeric.Implicits._
import scala.language.existentials
import scala.language.implicitConversions
import MaxFlow._
import com.raphtory.core.graph.visitor.Vertex

import scala.math.Ordering.Implicits.infixOrderingOps

/** {s}`MaxFlow[T](source: String, target: String, capacityLabel: String = "weight", maxIterations: Int = Int.MaxValue)`
  *   : Finds the maximum flow (equivalently, the minimum cut) between a source and a target vertex
  *
  *   Implements the parallel push-relabel max-flow algorithm of Goldberg and Tarjan. [^ref]
  *
  * ## Parameters
  *  {s}`T: Numeric`
  *    : Type of edge weight attribute (needs to be specified as not possible to infer automatically)
  *
  *  {s}`source: String`
  *    : name of source vertex
  *
  *  {s}`target: String`
  *    : name of target vertex
  *
  *  {s}`capacityLabel: String = "weight"`
  *    : Edge attribute key to use for computing capacities. Capacities are computed as the sum of weights over occurrences
  *      of the edge. If the edge property does not exist, weight is computed as the edge count.
  *
  *   {s}`maxIterations: Int = Int.MaxValue`
  *    : terminate the algorithm if it has not converged after {s}`maxIterations` pulses (note that the flow will be
  *      incorrect if this happens)
  *
  *  ## States
  *
  *  {s}`flow: mutable.Map[Long, T]`
  *    : Map of {s}`targetID -> flow`  for outflow at vertex (negative values are backflow used by the algorithm)
  *
  *  {s}`excess: T`
  *    : excess flow at vertex (should be 0 except for source and target after algorithm converged)
  *
  *  {s}`distanceLabel: Int`
  *    : vertex label used by the algorithm to decide where to push flow
  *
  *  {s}`neighbourLabels: mutable.Map[Long, Int]`
  *    : Map of {s}`targetID -> label` containing the distance labels for the vertexes neighbours
  *
  *  ## Returns
  *
  *  | Maximum Flow |
  *  | ------------ |
  *  | {s}`flow: T` |
  *
  *  ```{note}
  *  The algorithm returns a single line with the value of the maximum flow between the source and target.
  *  ```
  *
  * [^ref]: [A new approach to the Maximum-Flow Problem](http://akira.ruc.dk/~keld/teaching/algoritmedesign_f03/Artikler/08/Goldberg88.pdf)
  */

class MaxFlow[T](
    source: String,
    target: String,
    capacityLabel: String = "weight",
    maxIterations: Int = Int.MaxValue
)(implicit numeric: Numeric[T])
        extends GraphAlgorithm {

  override def apply(graph: GraphPerspective): GraphPerspective = {
    val n = graph.nodeCount()
    graph
      .step { vertex =>
        if (vertex.name() == source) {
          val flow = mutable.Map[Long, T]()
          vertex.setState("distanceLabel", n)
          vertex.getOutEdges().foreach { edge =>
            val c: T = edge.weight[T](capacityLabel)
            flow(edge.dst()) = c
            vertex.messageVertex(edge.dst(), FlowAdded(vertex.ID(), c))
          }
          vertex.setState("flow", flow)
          vertex.messageAllNeighbours(NewLabel(vertex.ID(), n))
        }
        else
          vertex.setState("distanceLabel", 0)

      }
      .iterate(
              { vertex =>
                val flow      = vertex.getOrSetState("flow", mutable.Map.empty[Long, T])
                val labels    = vertex.getOrSetState("neighbourLabels", mutable.Map.empty[Long, Int])
                var excess: T = vertex.getOrSetState[T]("excess", 0)
                vertex.messageQueue[Message].foreach {
                  case FlowAdded(source, value) =>
                    flow(source) = flow.getOrElse[T](source, 0) - value
                    excess += value

                  case NewLabel(source, label)  =>
                    labels(source) = label

                  case Recheck()                =>
                }
                if ((excess equiv 0) || vertex.name() == target || vertex.name() == source)
                  vertex.voteToHalt()
                else {
                  val label: Int = vertex.getState("distanceLabel")
                  // push operation
                  val outedges   = vertex.getOutEdges()
                  for (edge <- vertex.getOutEdges()) {
                    val dst = edge.dst()
                    if (label == labels.getOrElse(dst, 0) + 1) {
                      val c: T     = edge.weight(capacityLabel)
                      val res      = c - flow.getOrElse(dst, 0)
                      val delta: T = numeric.min(excess, res)
                      if (delta > 0) {
                        vertex.messageVertex(dst, FlowAdded(vertex.ID(), delta))
                        flow(dst) = flow.getOrElse[T](dst, 0) + delta
                        excess -= delta
                      }
                    }
                  }
                  // handle reverse flow
                  flow.foreach {
                    case (dst: Long, value: T) =>
                      if ((value < 0) && (label == (labels.getOrElse(dst, 0) + 1))) {
                        val delta: T = numeric.min(excess, -value)
                        if (delta > 0) {
                          vertex.messageVertex(dst, FlowAdded(vertex.ID(), delta))
                          flow(dst) += delta
                          excess -= delta
                        }
                      }
                  }

                  if (excess > 0) {
                    var newLabel = Int.MaxValue
                    for (edge <- vertex.getOutEdges()) {
                      val c: T = edge.weight(capacityLabel)
                      val dst  = edge.dst()
                      if (c - flow.getOrElse(dst, 0) > 0)
                        if ((labels.getOrElse(dst, 0) + 1) < newLabel)
                          newLabel = labels.getOrElse(dst, 0) + 1
                    }
                    flow.foreach {
                      case (dst, value) =>
                        if (value < 0)
                          if ((labels.getOrElse(dst, 0) + 1) < newLabel)
                            newLabel = labels.getOrElse(dst, 0) + 1
                    }
                    if (newLabel > label) {
                      vertex.setState("distanceLabel", newLabel)
                      vertex.messageAllNeighbours(NewLabel(vertex.ID(), newLabel))
                      vertex.messageSelf(Recheck())
                    }
                  }

                  vertex.setState("excess", excess)
                  vertex.setState("flow", flow)
                  vertex.setState("neighbourLabels", labels)
                }
              },
              maxIterations,
              executeMessagedOnly = true
      )
  }

  override def tabularise(graph: GraphPerspective): Table =
    graph.explodeSelect(vertex =>
      if (vertex.name() == source)
        List(Row(vertex.getState[mutable.Map[Long, T]]("flow").values.sum))
      else List.empty[Row]
    )

  sealed trait Message {}
  case class FlowAdded(source: Long, value: T)  extends Message
  case class NewLabel(source: Long, label: Int) extends Message
  case class Recheck()                          extends Message
}

object MaxFlow {

  def apply[T](
      source: String,
      target: String,
      capacityLabel: String = "weight",
      maxIterations: Int = Int.MaxValue
  )(implicit numeric: Numeric[T]): MaxFlow[T] =
    new MaxFlow(source, target, capacityLabel, maxIterations)(numeric)

  implicit def numericInt[T: Numeric](x: Int): T =
    implicitly[Numeric[T]].fromInt(x) // automatic conversion from Int for nicer syntax
}
