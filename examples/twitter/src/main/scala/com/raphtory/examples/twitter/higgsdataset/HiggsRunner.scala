package com.raphtory.examples.twitter.higgsdataset

import com.raphtory.Raphtory
import com.raphtory.algorithms.generic.centrality.{Degree, PageRank}
import com.raphtory.api.input.Source
import com.raphtory.examples.twitter.higgsdataset.analysis.MemberRank
import com.raphtory.examples.twitter.higgsdataset.analysis.TemporalMemberRank
import com.raphtory.examples.twitter.higgsdataset.graphbuilders.TwitterGraphBuilder
import com.raphtory.internals.graph.GraphBuilder
import com.raphtory.sinks.FileSink
import com.raphtory.spouts.FileSpout
import com.raphtory.utils.FileUtils


object HiggsRunner extends App {

  val path = "/tmp/higgs-retweet-activity.csv"
  val url  = "https://raw.githubusercontent.com/Raphtory/Data/main/higgs-retweet-activity.csv"
  FileUtils.curlFile(path, url)

  // Create Graph
  val spout  = FileSpout(path)
  val graph  = Raphtory.newGraph()
  val output = FileSink("/tmp/higgsoutput")
  val source = Source(spout, TwitterGraphBuilder.parse)

    graph.load(source)

  //get simple metrics
//    graph
//      .execute(Degree())
//      .writeTo(FileSink("tmp/raphtory"))
//      .waitForJob()

    graph
      .at(1341705593)
      .past()
      .execute(PageRank() -> MemberRank())
      .writeTo(output)
      .waitForJob()

  graph.close()
}
