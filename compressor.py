import sys
import json
from datetime import datetime
import os
import gzip
import notification

class compressor(object):
    ''' class compressor take as 1st argument name od configuration file
        and according to configuration than compress files in specified directory
        and if configured in subdirectory too
    '''
    
    def __init__(self, conf_file_name, now):
        ''' Initialization compressor class
            conf_file_name is name of configuration file
            now is datetime object whith time of starting this job
        '''
        self.conf_file_name = conf_file_name
        #print(self.conf_file_name)
        self.read_config(self.conf_file_name)
        self.ok = 0
        self.err = 0
        self.now = now
        self.searched_directories = []
        self.files_to_compress = []
        
    def read_config(self, path): 
        ''' Function reads configuration parameters for job
            path is name of config file if file is situated in the same directory or full path 
        '''
        with open(path) as conf_file:
            self.conf = json.load(conf_file)
            #print(self.conf)  
            
    def set_timestamp(self, date):
        ''' Function write time stamp of last compression job which ran to finish
            date is date of starting job
        '''
        timestamp_file_name = self.conf["job_name"] + "_timestamp.log"
        with open(timestamp_file_name, 'w') as timestamp_file:
            timestamp_file.write(date.strftime("%Y-%m-%d")+ '\n') 
            
    def get_timestamp(self):
        ''' Function return timestamp of last copress job
        '''
        timestamp_file_name = self.conf["job_name"] + "_timestamp.log"
        if os.path.exists(timestamp_file_name):
            try:
                with open(timestamp_file_name, "r") as timestamp_file:
                    last_job_str = timestamp_file.read().rstrip()
                    last_job = datetime.strptime(last_job_str,"%Y-%m-%d")
            except Exception as e:
                last_job = None
        else:
            last_job = None
        return(last_job)
            
    def is_job_maturate(self):
        '''detection if run compression job
           If explicitly time from last compression is lower than job_days_step in conf file so do not run.
           In all other case run compression (first time running, the job_days_step-th day regullary, 
           higher than it in case that server was shutdown, restart after crash)     
        '''
        run_job = True
        last_job = self.get_timestamp()
        if(last_job is not None):
            delta = self.now - last_job
            if(delta.days < self.conf["job_days_step"]):
                run_job = False    
        return run_job
        
    def set_suffix(self):
        ''' Function set suffix which may be append to file name if it is allowed in config file
        '''
        if(self.conf["add_date_suffix"]):
            self.suffix = self.now.strftime("%Y-%m-%d")
        else:
            self.suffix = ''
            
    def write_to_log(self, message):
        ''' Function writes to log file
        '''
        log_file_name = self.conf["job_name"] + ".log"
        with open(log_file_name, "a") as log_file:
            log_file.write(message)
            
    def find_files(self, directory):
        ''' Function search files in param directory.
            If recursion is allowed in config than search in subdir too.
            If file is real file (not link) than it is judge by extension.
            If its extension isnt in list of excluded extension than it will be compress.
            File may be without extension.
            directory is starting directory path 
        '''
        #on windows it will convert \\ to / (it is useful in test on win platform)
        #on linux it will have no effect
        directory = directory.replace(os.sep, '/')
        self.searched_directories.append(directory)
        
        with os.scandir(directory) as files:
            for file in files:
                #print(file.path)
                new_path = file.path.replace(os.sep, '/')
                if(file.is_dir()):
                    #print("je adresar" + new_path)
                    if(self.conf["recursive"]):
                        #print("zpracuj sub dir")
                        self.find_files(new_path)
                    continue
                
                if(file.is_file() and not file.is_symlink()):
                    #print("je soubor")
                    filename, extension = os.path.splitext(file.name)
                    #print("extension " + extension)
                    if(extension in self.conf["exclude_ext"]):
                        #print("vynechej")
                        continue
                    else:
                        self.files_to_compress.append(new_path)

    def compress_all(self):
        for file_to_compress in self.files_to_compress:
            new_compressed_file = self.get_compressed_file_name(file_to_compress)
            self.compress(file_to_compress)

    def compress(self, file_to_compress):
        ''' Function take file and compress it. After that remove original file.
            file_to_compress is full path to file 
        '''
        file_output_name = self.get_compressed_file_name(file_to_compress)
        try:
            with open(file_to_compress, "rb") as file_input:
                contant = file_input.read() 
                file_input.close()
                try:     
                    with gzip.open(file_output_name, 'wb') as file_output:        
                        file_output.write(contant)
                        self.ok = self.ok + 1
                        msg = "OK " + file_to_compress + "," + file_output_name + "\n" 
                        #print(msg) 
                        self.write_to_log(msg)
                        os.remove(file_to_compress)
                except Exception as e:
                    msg = "ERROR output:" + file_to_compress + "," + str(e) + "\n"
                    #print(msg)   
                    self.write_to_log(msg)
                    self.err = self.err + 1
        except Exception as e:
            msg = "ERROR input:" + file_to_compress + ", " + str(e) + "\n"
            #print(msg)   
            self.write_to_log(msg)
            self.err = self.err + 1

    def get_compressed_file_name(self, file_to_compress):  
        ''' Function get new name for compressed file.
            It may contain time suffix (recomended)
            file_to_compress is full path to file specified for compression
        '''
        return(file_to_compress + '-' + self.suffix + '.gz') 
     
    def write_final_stat(self):  
        ''' Function writes statistics to log after job
            and if set than send email notification to job owner
        '''             
        msg = "Job {0} finished OK. Compressed files {1}, error {2} \n".format(self.conf["job_name"], str(self.ok), str(self.err))
        print(msg)
        self.write_to_log(msg) 
        if(self.conf["inform_owner"]):
            notification1 = notification.notification(self.conf["sender_email"], self.conf["receiver_email"], self.conf["email_passwd"], self.conf["smtp_server"], self.conf["ssl_port"]) 
            notification1.prepare_message(msg) 
            notification1.sent() 
        
        
        
        
            
#####################################################        
if __name__ == '__main__':
    #set current working directory to directory with script
    #print(sys.argv)
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    #print(script_dir)
    os.chdir(script_dir)
    print("current working directory ", os.getcwd())
    
    now = datetime.now()
    compressor1 = compressor(sys.argv[1], now)    
    try:
        if(compressor1.is_job_maturate()):
            msg = "starting compress job " + str(now) + "\n"  
            #print(msg)
            compressor1.write_to_log(msg) 
            compressor1.find_files(compressor1.conf["direcrory"])
            #print(compressor1.files_to_compress)
            compressor1.set_suffix()
            compressor1.compress_all()
            compressor1.set_timestamp(now)
            compressor1.write_final_stat()
    except Exception as e:
        print("ERROR compress program error: " + str(e)) 