import java.io.{FileOutputStream, InputStream, OutputStream}
import java.net.{ServerSocket, Socket, InetAddress}
import scala.concurrent.Future
import scala.concurrent.ExecutionContext.Implicits.global
import scala.util.{Try, Success, Failure}

object Main extends App {
  val receivePort = 8080
  val savePath = "/Users/jomosmith/Desktop/Distributed Operating Systems/project/flappy/flappy/scala/quickstart/akka-quickstart-scala/"

  val serverSocket = new ServerSocket(receivePort, 0, InetAddress.getByName("0.0.0.0"))

  println("Scala server started")
  val hostName = InetAddress.getLocalHost.getHostName
  println("Host name: " + hostName)

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
      val in: InputStream = clientSocket.getInputStream
      val fileName: String = "trained_genome.pkl" // Generate a unique filename
      val fileOutput: OutputStream = new FileOutputStream(savePath + fileName)

      // Define the buffer size (e.g., 1024 bytes)
      val bufferSize: Int = 1024
      val buffer: Array[Byte] = new Array[Byte](bufferSize)

      var bytesRead: Int = 0

      // Read from input stream and write to file output stream
      while ({ bytesRead = in.read(buffer); bytesRead != -1 }) {
        fileOutput.write(buffer, 0, bytesRead)
      }

      fileOutput.close()
      clientSocket.close()

      println("File received and saved:", fileName)
      println("Client disconnected")
    }
  }
}
