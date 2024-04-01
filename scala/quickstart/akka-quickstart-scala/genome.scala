import java.io.{BufferedReader, InputStreamReader, PrintWriter}
import java.net.{ServerSocket, Socket, InetAddress}
import play.api.libs.json._
import scala.concurrent.Future
import scala.concurrent.ExecutionContext.Implicits.global
import scala.util.{Try, Success, Failure}

case class Node(key: Int, bias: Double, response: Int, activation: String, aggregation: String)
object Node {
  implicit val nodeFormat: Format[Node] = Json.format[Node]
}

case class Connection(key: List[Int], weight: Double, enabled: Boolean)
object Connection {
  implicit val connectionFormat: Format[Connection] = Json.format[Connection]
}

case class Genome(key: Int, fitness: Option[Double], nodes: List[Node], connections: List[Connection])
object Genome {
  implicit val genomeFormat: Format[Genome] = Json.format[Genome]
}

object Main extends App {
  val receivePort = 8080
  val sendPort = 8081
  val serverSocket = new ServerSocket(receivePort)
  println("Scala server started")
  val hostName = InetAddress.getLocalHost.getHostName
  println("Host name: " + hostName)
  var count = 0

  while (true) {
    val clientSocket = Try(serverSocket.accept()) match {
      case Success(socket) => socket
      case Failure(exception) =>
        println("Error accepting connection:", exception)
        serverSocket.close()
        sys.exit(1)
    }
    println("Client connected")

    Future {
      val in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream))

      val receivedGenomes = scala.collection.mutable.ListBuffer[Genome]()

      var line: String = null
      while ({line = in.readLine(); line != null}) {
        val json = Json.parse(line)
        val genomeKey = (json \ "key").as[Int]
        val fitness = (json \ "fitness").asOpt[Double].getOrElse(0.0)
        val nodes = (json \ "nodes").as[List[Node]]
        val connections = (json \ "connections").as[List[Connection]]
        println("RECEIVING GENOMES")
        receivedGenomes += Genome(genomeKey, Some(fitness), nodes, connections)
      }

      clientSocket.close()
      println("Client disconnected")

      // Send genomes to the specified host and port
      val sendSocket = new Socket(InetAddress.getLocalHost, sendPort)
      val out = new PrintWriter(sendSocket.getOutputStream, true)

      for (genome <- receivedGenomes) {
        val fitness = evaluateGenome(genome.nodes, genome.connections)
        count += 1
        val responseData = Json.toJson(genome.copy(fitness = Some(fitness)))
        println("SENDING GENOMES")
        out.println(Json.stringify(responseData))
      }

      out.close()
      sendSocket.close()
    }
  }

  def evaluateGenome(nodes: List[Node], connections: List[Connection]): Double = {
    val biasSum = nodes.map(_.bias).sum
    biasSum
  }

  val thresholdFitness = 0.0
}
