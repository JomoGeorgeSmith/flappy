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
  val serverSocket = new ServerSocket(receivePort, 0, InetAddress.getByName("0.0.0.0"))

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
    // Get the client's IP address
    val clientAddress = clientSocket.getInetAddress.getHostAddress
    println(s"Client connected from IP address: $clientAddress")

    Future {
      val in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream))

      val receivedGenomes = scala.collection.mutable.ListBuffer[Genome]()

      var line: String = null
      while ({line = in.readLine(); line != null}) {
        val json = Json.parse(line)
        val genome = json.as[Genome]
        println("RECEIVING GENOMES")
        receivedGenomes += genome
      }

      clientSocket.close()
      println("Client disconnected")

      // Send received genomes to the specified host and port
      val sendSocket = new Socket(InetAddress.getLocalHost, sendPort)
      val out = new PrintWriter(sendSocket.getOutputStream, true)

      for (genome <- receivedGenomes) {
        count += 1
        val responseData = Json.toJson(genome)
        println("SENDING GENOMES")
        println(responseData)
        out.println(Json.stringify(responseData))
      }

      out.close()
      sendSocket.close()
    }
  }
}
