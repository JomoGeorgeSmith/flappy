import akka.actor.{Actor, ActorSystem, Props}
import java.io.{File, FileInputStream, FileOutputStream, InputStream, OutputStream}
import java.net.{ServerSocket, Socket, InetAddress}
import scala.concurrent.Future
import scala.concurrent.ExecutionContext.Implicits.global
import scala.util.{Try, Success, Failure}

object Main extends App {
  val receivePort = 8080
  val sendPort = 8081 // Port for sending the file
  val savePath = "/Users/jomosmith/Desktop/Distributed Operating Systems/project/flappy/flappy/scala/quickstart/akka-quickstart-scala/"

  // Create an actor system
  val system = ActorSystem("ReceiveActorSystem")

  // Create an instance of ReceiveActor
  val receiveActor = system.actorOf(Props(new ReceiveActor(savePath)), "receiveActor")

  // Create an instance of SendActor
  val sendActor = system.actorOf(Props(new SendActor(savePath)), "sendActor")

  // Start the server
  val server = new Server(receivePort, receiveActor, sendPort)
  server.start()
}

class Server(receivePort: Int, receiveActor: akka.actor.ActorRef, sendPort: Int) {
  val serverSocket = new ServerSocket(receivePort, 0, InetAddress.getByName("0.0.0.0"))

  println("Scala server started")
  val hostName = InetAddress.getLocalHost.getHostName
  println("Host name: " + hostName)

  def start(): Unit = {
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

      // Check if the request is for sending the file
      if (clientSocket.getPort == sendPort) {
        // Send clientSocket to the SendActor
        receiveActor ! clientSocket
      } else {
        // Send clientSocket to the ReceiveActor
        receiveActor ! clientSocket
      }
    }
  }
}

class ReceiveActor(savePath: String) extends Actor {
  def receive: Receive = {
    case (clientSocket: Socket, "REQUEST_GENOME") =>
      Future {
        val fileName: String = "trained_genome.pkl"
        val filePath: String = savePath + fileName
        val file = new File(filePath)

        if (file.exists()) {
          val out: OutputStream = clientSocket.getOutputStream
          val fis = new FileInputStream(file)
          val bufferSize: Int = 1024
          val buffer: Array[Byte] = new Array[Byte](bufferSize)
          var bytesRead = 0

          // Send the file over the socket
          while ({ bytesRead = fis.read(buffer); bytesRead != -1 }) {
            out.write(buffer, 0, bytesRead)
          }

          fis.close()
          out.close()
          clientSocket.close()

          println("File sent:", fileName)
          println("Client disconnected")
        } else {
          println("File does not exist:", fileName)
          clientSocket.close()
        }
      }
    case clientSocket: Socket =>
      Future {
        val in: InputStream = clientSocket.getInputStream
        val fileName: String = "trained_genome.pkl" // Or any desired filename
        val filePath: String = savePath + fileName
        val fileOutput: OutputStream = new FileOutputStream(filePath)

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

class SendActor(savePath: String) extends Actor {
  def receive: Receive = {
    case (clientSocket: Socket, "SEND_GENOME") =>
      Future {
        val fileName: String = "trained_genome.pkl"
        val filePath: String = savePath + fileName
        val file = new File(filePath)

        if (file.exists()) {
          val out: OutputStream = clientSocket.getOutputStream
          val fis = new FileInputStream(file)
          val bufferSize: Int = 1024
          val buffer: Array[Byte] = new Array[Byte](bufferSize)
          var bytesRead = 0

          // Send the file over the socket
          while ({ bytesRead = fis.read(buffer); bytesRead != -1 }) {
            out.write(buffer, 0, bytesRead)
          }

          fis.close()
          out.close()
          clientSocket.close()

          println("File sent:", fileName)
          println("Client disconnected")
        } else {
          println("File does not exist:", fileName)
          clientSocket.close()
        }
      }
  }
}
