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
  val system = ActorSystem("FileTransferActorSystem")

  // Create an instance of FileTransferActor
  val fileTransferActor = system.actorOf(Props(new FileTransferActor(savePath)), "fileTransferActor")

  // Start the servers
  val receiveServer = new FileTransferServer(receivePort, fileTransferActor)
  val sendServer = new FileTransferServer(sendPort, fileTransferActor)
  receiveServer.start()
  sendServer.start()
}

class FileTransferServer(port: Int, fileTransferActor: akka.actor.ActorRef) {
  private val serverSocket = new ServerSocket(port, 0, InetAddress.getByName("0.0.0.0"))

  println(s"Scala server started on port $port")
  val hostName = InetAddress.getLocalHost.getHostName
  println("Host name: " + hostName)

  def start(): Unit = {
    Future {
      while (true) {
        val clientSocket = Try {
          serverSocket.accept()
        } match {
          case Success(socket) => socket
          case Failure(exception) =>
            println("Error accepting connection:", exception)
            serverSocket.close()
            sys.exit(1)
        }

        // Get the client's IP address
        val clientAddress = clientSocket.getInetAddress.getHostAddress
        println(s"Client connected from IP address: $clientAddress")
        println(clientSocket.getLocalPort)

        // Route the clientSocket to the appropriate actor based on the port
        if (port == Main.sendPort) {
          println("SENDING")
          // Send clientSocket to the FileTransferActor with the request type "SEND_GENOME"
          fileTransferActor ! (clientSocket, "SEND_GENOME")
        } else {
          // Send clientSocket to the FileTransferActor with the request type "RECEIVE_GENOME"
          fileTransferActor ! (clientSocket, "RECEIVE_GENOME")
        }
      }
    }
  }
}

class FileTransferActor(savePath: String) extends Actor {
  def receive: Receive = {
    case (clientSocket: Socket, "RECEIVE_GENOME") =>
      // Handle receiving file
      receiveFile(clientSocket)
    case (clientSocket: Socket, "SEND_GENOME") =>
      // Handle sending file
      sendFile(clientSocket)
    case _ =>
      println("Unsupported request type")
  }

  def receiveFile(clientSocket: Socket): Unit = {
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

def sendFile(clientSocket: Socket): Unit = {
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
      out.write("READY\n".getBytes) // Send "READY" message to client
      while ({ bytesRead = fis.read(buffer); bytesRead != -1 }) {
        out.write(buffer, 0, bytesRead)
      }

      // Send confirmation message to indicate file transfer completion
      out.write("GENOME_SENT\n".getBytes)

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
