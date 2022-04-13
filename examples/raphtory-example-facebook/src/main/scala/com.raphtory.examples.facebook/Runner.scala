package com.raphtory.examples.facebook

import com.raphtory.algorithms.generic.ConnectedComponents
import com.raphtory.algorithms.generic.EdgeList
import com.raphtory.deployment.Raphtory
import com.raphtory.output.FileOutputFormat
import com.raphtory.output.PulsarOutputFormat
import com.raphtory.examples.facebook.graphbuilders.FacebookGraphBuilder
import com.raphtory.spouts.StaticGraphSpout
import com.typesafe.config

import java.io.File
import scala.language.postfixOps
import sys.process._

object Runner extends App {

  // Create Graph

  if (!new File("/tmp", "facebook.csv").exists()) {
    val path = "/tmp/facebook.csv"
    try s"curl -o $path https://raw.githubusercontent.com/Raphtory/Data/main/facebook.csv " !!
    catch {
      case ex: Exception =>
        println(s"Failed to download 'facebook.csv' due to ${ex.getMessage}.")
        ex.printStackTrace()

        (s"rm $path" !)
        throw ex
    }
  }
  val conf: config.Config = Raphtory.getDefaultConfig()

  val source: StaticGraphSpout = StaticGraphSpout("/tmp/facebook.csv")
  val builder                  = new FacebookGraphBuilder()
  val graph                    = Raphtory.batchLoadGraph(spout = source, graphBuilder = builder)
  Thread.sleep(20000)
  graph.pointQuery(EdgeList(), PulsarOutputFormat("EdgeList"), timestamp = 88234)
  graph.rangeQuery(
          ConnectedComponents(),
          PulsarOutputFormat("ConnectedComponents"),
          10000,
          88234,
          10000,
          List(500, 1000, 10000)
  )

}
