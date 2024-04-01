import java.io.{BufferedReader, InputStreamReader, PrintWriter}
import java.net.{ServerSocket, Socket, InetAddress}
import play.api.libs.json._

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
  val port = 8080
  val serverSocket = new ServerSocket(port)
  println("Scala server started")
  val hostName = InetAddress.getLocalHost.getHostName
  println("Host name: " + hostName)
  var count = 0

  while (true) {
    val clientSocket = serverSocket.accept()
    println("Client connected")

    val in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream))
    val out = new PrintWriter(clientSocket.getOutputStream, true)

    val receivedGenomes = scala.collection.mutable.ListBuffer[Genome]()

    var line: String = null
    while ({line = in.readLine(); line != null}) {
      val json = Json.parse(line)
      val genomeKey = (json \ "key").as[Int]
      val fitness = (json \ "fitness").asOpt[Double].getOrElse(0.0)
      val nodes = (json \ "nodes").as[List[Node]]
      val connections = (json \ "connections").as[List[Connection]]
      println("RECEIVINg GENOMES")
      receivedGenomes += Genome(genomeKey, Some(fitness), nodes, connections)
    }

    for (genome <- receivedGenomes) {
      val fitness = evaluateGenome(genome.nodes, genome.connections)
      count += 1
      val responseData = Json.toJson(genome.copy(fitness = Some(fitness)))
      println("SENDING GENOMES")
      out.println(Json.stringify(responseData))
    }

    in.close()
    out.close()
    clientSocket.close()
    println("Client disconnected")
  }

  def evaluateGenome(nodes: List[Node], connections: List[Connection]): Double = {
    val biasSum = nodes.map(_.bias).sum
    biasSum
  }

  val thresholdFitness = 0.0
}
