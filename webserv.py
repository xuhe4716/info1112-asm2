
import sys
import socket
import os
import gzip



class Server:
    def __init__(self,configfile):
        self.configfile = configfile
        self.host = socket.gethostbyname(socket.gethostname())
        self.client = ""

        self.staticfiles = ""
        self.cgibin = ""
        self.port = ""
        self.exec = ""
        
        self.method = ""
        self.resource = ""
        self.protocol = ""
        self.response = ""
        self.path = ""

        self.query_string = ""
        self.status = ""
        self.compressed = False
        



        self.request_dict = {"Accept" : "", "Host" : "","User-Agent": "", "Accept-Encoding" : "", "Remote-Address" : "", "Content-Type" : "", "Content-Length" : ""}
        self.content_type_dict = {".txt" : "text/plain", ".html" : "text/html", ".js" : "application/javascript", ".css" : "text/css", ".png" : "image/png", ".jpg" : "image/jpeg", ".jpeg" : "image/jpeg", ".xml" : "text/xml"}


    def readConfig(self, filename):
        '''
        TODO
            Read config file and set port, static files, cgibin and exec
        :param filename: config file
        :return:
        '''
        config = {"staticfiles" : "initialization", "cgibin": "initialization", "port" : "initialization", "exec" : "initialization"}
        try:
            f = open(filename)
            lines = f.readlines()
            i=0
            while i< len(lines):
                lines_split = lines[i].split("=")
                config[lines_split[0]] = lines_split[1].strip()
                i+=1
        except FileNotFoundError:
            print("Unable To Load Configuration File")
            exit(1)

        for value in config.values():
            if value == "initialization":
                print("Missing Field From Configuration File")
                exit(1)
        

        self.port = int(config["port"])
        self.staticfiles = config["staticfiles"]
        self.cgibin = config["cgibin"]
        self.exec = config["exec"]
    





    def start(self):
        '''
        TODO
            Initialize the socket and listen begin
        :return:
        '''
        self.readConfig(self.configfile)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.host, self.port))
        print("bind successfully")
        self.listen()
        


    def listen(self):
        '''
        TODO
            Accept and decode the request, parse request and send the response back, and finally close the connection
        :return:
        '''
        self.socket.listen()
        while True:
            (client, address) = self.socket.accept()
            self.client = str(client)
            request_msg = client.recv(1024).decode()
            self.parse_request(request_msg)
            pid = os.fork()
            if pid == 0:
                if self.response != "":
                    client.send(self.response)
                client.close()

            else:
                os.wait
                client.close()




    def set_enviroment(self):
        '''
        TODO
            Set CGI environment variables
        :return:
        '''
        if self.request_dict["Accept"] != "":
            os.environ['HTTP_ACCEPT'] = self.request_dict["Accept"]
        if self.request_dict["Host"] != "":
            os.environ['HTTP_HOST'] = self.request_dict["Host"]
        if self.request_dict["User-Agent"] !="":
            os.environ['HTTP_USER_AGENT'] = self.request_dict["User-Agent"]
        if self.request_dict["Accept-Encoding"] != "":
            os.environ['HTTP_ACCEPT_ENCODING'] = self.request_dict["Accept-Encoding"]
        
        client_str = str(self.client).split("raddr=(")[1].replace("'","").replace(")>","").split(",")

        os.environ['REMOTE_ADDRESS'] = client_str[0]
        os.environ['REMOTE_PORT'] = client_str[1]
        os.environ['REQUEST_METHOD'] = self.method
        os.environ['REQUEST_URI'] = self.resource
        os.environ['SERVER_ADDR'] = self.host
        os.environ['SERVER_PORT'] = str(self.port)

        if self.query_string != "":
            os.environ['QUERY_STRING'] = self.query_string
            
        if self.method == "POST":
            if self.request_dict["Content-Type"] != "":
                os.environ['CONTENT_TYPE'] = self.request_dict["Content-Type"]
            if self.request_dict["Content-Length"] != "":
                os.environ['CONTENT_LENGTH'] = self.request_dict["Content-Length"]


    def compress_msg(self, msg, image):
        '''
        TODO
            Compress a msg and read it as binary
        :param msg: msg need to be compressed
        :param image: input is an image or not
        :return: A binary msg
        '''
        f= gzip.open('body.txt.gz', 'wb')
        if image == True:
            f.write(msg)
        else:
            f.write(msg.encode())
        f.close
        f = open("body.txt.gz", "rb")
        compressed_content = f.read()
        f.close()
        return compressed_content


    def parse_request(self, msg):
        '''
        TODO
            Parse HTTP request, assign them to self variable
        :param msg: HTTP Request
        :return:
        '''
        newmsg = msg.strip().replace("\r","").split("\n")
        head_msg = newmsg[0].split(" ")
        self.method = head_msg[0]
        self.resource = head_msg[1]
        self.protocol = head_msg[2]
        
        for each in newmsg:
            split_each = each.split(": ")
            for key in self.request_dict.keys():
                if key == split_each[0]:
                    self.request_dict[key] = split_each[1]
                    
        if "gzip" in self.request_dict["Accept-Encoding"]:
            self.compressed = True
        else:
            self.compressed = False
            
        
        self.parse_resource(self.resource)
        
        


    def parse_resource(self, resource_msg):
        '''
        TODO
            Parse the resource from HTTP request, assign them to self variable
        :param msg: Resource from HTTP Request
        :return:
        '''
        if "?" in resource_msg:
            resource_split = resource_msg.split("?")
            self.resource = resource_split[0]
            self.query_string = resource_split[1]
            

        

        if ("./" + self.resource.split("/")[1]) == self.cgibin:
            self.path = self.cgibin + "/" + self.resource.split("/")[2]
            self.set_enviroment()
            self.run_program(self.exec,self.path)
            return

        if resource_msg == "/":
            self.request_dict["Content-Type"] = "text/html"
            self.path = self.staticfiles + "/" + "index.html"
            self.readfiles()
        else:
            resource_split = self.resource.split(".")
            if ("." + resource_split[1]) in self.content_type_dict.keys():
                self.request_dict["Content-Type"] = self.content_type_dict["." + resource_split[1]]
                self.path = self.staticfiles + self.resource
                self.readfiles()
                

        


    def run_program(self, path, argv):
        '''
        TODO
            Run file in cgi bin
        :param path: self.exec
        :param argv: self.path
        :return:
        '''
        body = ""
        try:
            read_p,write_p = os.pipe() #make read file and write file
            if os.fork() == 0:
                os.dup2(write_p, 1) #write the output in to write_p
                os.execve(path, [path, argv], os.environ) #run program
                sys.exit(1) #if error occur, exit(1)
            check = os.wait()
            if check[1] != 0:
                self.status = "500 Internal Server Error"
                raise Exception
            else:
                self.status = "200 OK"
                
            os.close(write_p) #close write file
            result = os.fdopen(read_p) #read output
            body = "".join(result)
        except Exception as e:
            self.status = "500 Internal Server Error"
        
        

        if self.status != "500 Internal Server Error":
            if "Status-Code:" in body:
                self.status = body.split("Status-Code: ")[1]
            head = self.protocol + " " + self.status +"\n"

            if "Content-Type" in body:
                if self.compressed == True:
                    body = self.compress_msg(body, False)
                    self.response = (head).encode()
                    self.response += body
                else:
                    self.response = head + body
                    self.response = self.response.encode()
                    
                    
                self.response = (head + body).encode()
                
            else:
                if self.compressed == True:
                    body = self.compress_msg(body, False)
                    self.response = (head + "\n").encode()
                    self.response += body

                else:
                    self.response = head + "\n" + body
                    self.response = self.response.encode()
        
        else:
            head = self.protocol + " " + self.status +"\n"
            self.response = head
            self.response = self.response.encode()



            

    def readfiles(self):
        '''
        TODO
            Parse file in static files
        :return:
        '''
        request = ""
        for key, value in self.request_dict.items():
            if value:
                request += "{}: {}\n".format(key, value)

        body = ""
        try:
            if "image" in self.request_dict["Content-Type"].split("/"):
                f = open(self.path, "rb").read()
                self.status = "200 OK"
                head = self.protocol + " " + self.status +"\n"
                if (self.compressed == True):
                    head = (head +request + "\n").encode() + self.compress_msg(f,True)
                else:
                    head = (head +request + "\n").encode() + f
                self.response = head
                return


            else:
                f = open(self.path).readlines()
                for each in f:
                    body += each

            self.status = "200 OK"

        except FileNotFoundError:
            body = '<html>\n<head>\n\t<title>404 Not Found</title>\n</head>\n<body bgcolor="white">\n<center>\n\t<h1>404 Not Found</h1>\n</center>\n</body>\n</html>\n'
            self.status = "404 File not found"
            
        head = self.protocol + " " + self.status +"\n"
        
        if self.compressed == True:
            body = self.compress_msg(body,False)
            self.response = (head + request + "\n").encode()
            self.response += body
            
        else:
            self.response = head + request + "\n"+body
            self.response = self.response.encode()

        
    
    
        
        






def main():
    try:
        config_name = sys.argv[1]
    except Exception:
        print("Missing Configuration Argument")  # if no config file is given
        exit(1)

    server = Server(config_name)  # Initialize the server
    server.start()




if __name__ == '__main__':
    main()
