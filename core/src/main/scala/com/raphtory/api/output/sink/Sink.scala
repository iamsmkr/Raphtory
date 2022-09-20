package com.raphtory.api.output.sink

import com.raphtory.api.analysis.table.Row
import com.raphtory.api.time.Perspective
import com.raphtory.internals.communication.TopicRepository
import com.raphtory.sinks.FileSink
import com.typesafe.config.Config
import com.typesafe.scalalogging.Logger
import org.slf4j.LoggerFactory

/** Base trait for sinks.
  *
  * A sink defines a way to output a table generated by Raphtory from a graph.
  * In order to do this, concrete implementations need to override the `executor` method creating their own `SinkExecutor`.
  * This is the class holding the actual code required to connect and output to the sink.
  *
  * @see [[com.raphtory.sinks.FileSink FileSink]], [[PulsarSink PulsarSink]],
  *      [[com.raphtory.api.analysis.table.Table Table]]
  */
trait Sink {

  /**
    * @param jobID the ID of the job that generated the table
    * @param partitionID the ID of the partition of the table
    * @param config the configuration provided by the user
    * @param topics the topic repository of the deployment
    * @return the `SinkExecutor` to be used for writing out results
    */
  def executor(jobID: String, partitionID: Int, config: Config, topics: TopicRepository): SinkExecutor
}

/** Base trait for sink executors.
  *
  * Concrete implementations need to override the `setupPerspective`, `writeRow`, `closePerspective`, and `close`
  * methods.
  *
  *  @see [[com.raphtory.api.analysis.table.Row Row]], [[com.raphtory.api.time.Perspective Perspective]]
  */
trait SinkExecutor {

  /** Logger instance for writing debug messages */
  protected lazy val logger: Logger = Logger(LoggerFactory.getLogger(this.getClass))

  /** Sets up the perspective to be written out.
    * This method gets called every time a new graph perspective is going to be written out so this `SinkExecutor` can
    * handle it if needed.
    * @param perspective the perspective to be written out
    */
  def setupPerspective(perspective: Perspective): Unit

  /** Writes out one row.
    * The implementation of this method doesn't need to be thread-safe as it is wrapped by `threadSafeWriteRow` to
    * handle synchronization.
    * @param row the row of data to write out
    */
  protected def writeRow(row: Row): Unit

  /** Closes the writing of the current graph perspective.
    * This method gets called every time all the rows from one graph perspective have been successfully written out so
    * this `SinkExecutor` can handle it if needed.
    */
  def closePerspective(): Unit

  /** Closes this `SinkExecutor` after writing the complete table.
    *
    * This method should free up all the resources in use.
    */
  def close(): Unit

  /** Thread safe version of `writeRow` used internally by Raphtory to write a `row`.
    * Override this method to provide a more efficient thread-safe implementation.
    */
  def threadSafeWriteRow(row: Row): Unit = synchronized(writeRow(row))
}
