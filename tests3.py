import unittest
import compressor
from datetime import datetime
from datetime import timedelta
import os.path
import random
import string

class TestCompressor(unittest.TestCase):

#############################################################
# tests 

    def test_maturation_is_precisely(self):
        ''' Tests if compression task will start precisely N-th day after last job.  
            Default in conf file is 30
        '''
        tested_data = ("2019-01-01","2019-01-02","2019-10-25","2019-11-30","2019-12-01","2019-12-31")
        for x in tested_data:
            now = datetime.strptime(x,"%Y-%m-%d")
            compressor1 = compressor.compressor("job1.conf", now)
            self.clear_environment(compressor1.conf)
            diff = timedelta(days=compressor1.conf["job_days_step"])
            last_date = now - diff 
            compressor1.set_timestamp(last_date)
            result = compressor1.is_job_maturate() 
            self.assertEqual(result, True, 'it didnt run a job after enough days')
        
    def test_maturation_is_higher(self):
        ''' Tests situation that server was shutdown in time when job was planed. May be plan was 30th day.
            After repearing sever cron will start program. It is higher than 30th, but compression should be done
        '''
        tested_data = ("2019-01-01","2019-01-02","2019-10-25","2019-11-30","2019-12-01","2019-12-31")
        for x in tested_data:
            now = datetime.strptime(x,"%Y-%m-%d")
            compressor1 = compressor.compressor("job1.conf", now)
            self.clear_environment(compressor1.conf)
            diff = timedelta(days=compressor1.conf["job_days_step"] + 1)
            last_date = now - diff 
            compressor1.set_timestamp(last_date)
            result = compressor1.is_job_maturate() 
            self.assertEqual(result, True, 'it didnt run a job after enough days')
            
    def test_maturation_is_lower(self):
        ''' In days before plan compression must not be done. 
            Tests 1 day before plan.
        '''
        tested_data = ("2019-01-01","2019-01-02","2019-10-25","2019-11-30","2019-12-01","2019-12-31")
        for x in tested_data:
            now = datetime.strptime(x,"%Y-%m-%d")
            compressor1 = compressor.compressor("job1.conf", now)
            self.clear_environment(compressor1.conf)
            diff = timedelta(days=compressor1.conf["job_days_step"] - 1)
            last_date = now - diff 
            compressor1.set_timestamp(last_date)
            result = compressor1.is_job_maturate() 
            self.assertEqual(result, False, 'it run a job before maturation') 
            
    def test_first_time_run_job(self):
        ''' In first time job will start file with timestamp dosnt exist. In such case compression must start.
        '''
        tested_data = ("2019-01-01","2019-01-02","2019-10-25","2019-11-30","2019-12-01","2019-12-31")
        for x in tested_data:
            now = datetime.strptime(x,"%Y-%m-%d")
            compressor1 = compressor.compressor("job1.conf", now)
            #before first run dosnt exist file with timestamp, it is prepared in clear_environment too 
            self.clear_environment(compressor1.conf)
            #but for case that clear_environment will be modified I explicitly check it
            timestamp_file_name = compressor1.conf["job_name"] + "_timestamp.log"
            if(os.path.exists(timestamp_file_name)):          
                os.remove(timestamp_file_name)
            result = compressor1.is_job_maturate() 
            self.assertEqual(result, True, 'first time run wasnt started') 
            
    def test_set_suffix1(self):
        ''' Tests that if configured by admin that suffix will be append to compressed file
        '''
        now = datetime.strptime("2019-01-01","%Y-%m-%d")
        compressor1 = compressor.compressor("job1.conf", now)
        self.clear_environment(compressor1.conf)
        compressor1.conf["add_date_suffix"] = True
        compressor1.set_suffix()
        self.assertEqual(compressor1.suffix, '2019-01-01', 'bad suffix settings')
            
    def test_set_suffix2(self):
        ''' Test case than time suffix admin dont want to compressed file
        '''
        now = datetime.strptime("2019-01-01","%Y-%m-%d")
        compressor1 = compressor.compressor("job1.conf", now)
        self.clear_environment(compressor1.conf)
        compressor1.conf["add_date_suffix"] = False
        compressor1.set_suffix()
        self.assertEqual(compressor1.suffix, '', 'bad suffix settings')
            
    def test_recursive_searching(self):
        ''' Test case that recusive searching in dir tree is done if admin configured it.
        '''
        now = datetime.strptime("2019-12-01","%Y-%m-%d")
        compressor1 = compressor.compressor("job1.conf", now)
        self.clear_environment(compressor1.conf)
        compressor1.conf["recursive"] = True
        self.create_subdir_tree(compressor1.conf["direcrory"])
        compressor1.find_files(compressor1.conf["direcrory"])
        #print(self.subdirs)
        for subd in self.subdirs:
            self.assertIn(subd, compressor1.searched_directories, 'subdir wasnt searched')
        
    
    def test_not_recursive_searching(self):
        ''' Test case that recusive searching in dir tree is not allowed. 
        '''
        now = datetime.strptime("2019-12-01","%Y-%m-%d")
        compressor1 = compressor.compressor("job1.conf", now)
        self.clear_environment(compressor1.conf)
        compressor1.conf["recursive"] = False
        self.create_subdir_tree(compressor1.conf["direcrory"])
        compressor1.find_files(compressor1.conf["direcrory"])
        #print(self.subdirs)
        for subd in self.subdirs:
            self.assertNotIn(subd, compressor1.searched_directories, 'subdir wasnt searched') 

            
    def test_searching_files(self):
        ''' test if all files for compression will be find
        '''
        now = datetime.strptime("2019-12-01","%Y-%m-%d")
        compressor1 = compressor.compressor("job1.conf", now)
        self.clear_environment(compressor1.conf)
        compressor1.conf["recursive"] = True
        self.create_subdir_tree(compressor1.conf["direcrory"])
        self.create_all_random_files(compressor1.conf["exclude_ext"], compressor1.conf["direcrory"])
        compressor1.find_files(compressor1.conf["direcrory"]) 
        #test that files with extension for exclusion are really excluded
        for afile in self.files_exclude:
            self.assertNotIn(afile, compressor1.files_to_compress, 'file should be excluded and wasnt')   
        #test that all files for compression are really find
        #print(compressor1.files_to_compress)
        for afile in self.files_compress:
            self.assertIn(afile, compressor1.files_to_compress, 'file should be compress and isnt')     
        


    def test_compression(self):
        ''' Tests if files which are specified for compression are really compressed and 
            after that are original files deleted
        '''
        now = datetime.strptime("2019-12-01","%Y-%m-%d")
        compressor1 = compressor.compressor("job1.conf", now)
        self.clear_environment(compressor1.conf)
        compressor1.conf["recursive"] = True
        self.create_subdir_tree(compressor1.conf["direcrory"])
        self.create_all_random_files(compressor1.conf["exclude_ext"], compressor1.conf["direcrory"])
        compressor1.find_files(compressor1.conf["direcrory"])
        compressor1.set_suffix()
        for file_to_compress in compressor1.files_to_compress:
            new_compressed_file = compressor1.get_compressed_file_name(file_to_compress)
            compressor1.compress(file_to_compress)
            self.assertTrue(os.path.exists(new_compressed_file), "new compressed file wasnt created")
            self.assertFalse(os.path.exists(file_to_compress), "old file after compression wasnt deleted")
            
            
            
#############################################################
# operation functions             
        
    def create_subdir_tree(self, rootdir):
        ''' Function create subdirectory tree for testing purpose
            rootdir is starting directory specified in config file
        ''' 
        subdirs = ["subdir1"]
        subdirs.append("subdir2")
        subdirs.append("subdir2/subdir21")
        subdirs.append("subdir2/subdir22")
        self.subdirs = []
        for directory in subdirs:
            dir_name = rootdir + "/" + directory
            #print(dir_name)
            self.subdirs.append(dir_name)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                
    def create_random_file_name(self):
        ''' Function return random name for files which are generated for testing.
        '''
        letters = string.ascii_lowercase
        return(''.join(random.choice(letters) for i in range(6))) 
        
    def create_random_file_full_name(self, path, ext):
        ''' Function return full path for files which are generated for testing.
        '''
        file_full_name = path + '/' + self.create_random_file_name() + ext
        return(file_full_name)
        
    def create_all_random_files(self, conf_exclude_extensions, root_path):
        ''' Function generates testing files.
            Created files has extensions both categories - for excluding and for compression (and without extension)
        '''
        self.files_exclude = []
        self.files_compress = []
        #use all extensions in config files
        all_ext = []
        exclude_extensions = []
        for x in conf_exclude_extensions:
            all_ext.append(x)
            exclude_extensions.append(x)
        #and without duplicity use these ext too for exclusion
        ext_exclusion_add = [".gz",".Z"]
        for x in ext_exclusion_add:
            if(x not in all_ext):
                all_ext.append(x)
                exclude_extensions.append(x)
        #and use these this for test compression
        ext_add_not_excluded = [".jpg", ".txt", ""]
        for x in ext_add_not_excluded:
            if(x not in all_ext):
                all_ext.append(x)
        #print("exclude_extensions {0}".format(exclude_extensions))
        #print("all_ext {0}".format(all_ext))
        #only dirs created for tests
        dirs = self.subdirs
        #add path to root where files need to be created too
        dirs.append(root_path)
        #create files for test purposes
        for adir in dirs:
            for aext in all_ext:
                file_name = self.create_random_file_full_name(adir, aext)
                #print(file_name)
                #select files to two groups - for exclusion and compression
                if(aext in exclude_extensions):
                    self.files_exclude.append(file_name)
                else:
                    self.files_compress.append(file_name)
                #add some contant to files
                with open(file_name, "a") as f:
                    for i in range(10):
                        f.write("nejaky text")
 
        #print(self.files_exclude)
        #print(self.files_compress)

        
    def clear_files(self, root_job_path):
        ''' Function before every test deletes all files
        '''
        with os.scandir(root_job_path) as files:
            for file in files:
                #print(file.path)
                if(file.is_dir()):
                    self.clear_files(file.path)
                    continue
                if(file.is_file() and not file.is_symlink()):
                    os.remove(file.path) 
 
    def delete_timestamp(self, timestamp_file_name):  
        ''' Function before every test delete timestamp file
            (If file is needed for test than it will be explicitely created in test)
        '''  
        if(os.path.exists(timestamp_file_name)):
            try:
                os.remove(timestamp_file_name)
            except Exception as e:
                print("cant delete timestamp file " + e)
                
        
    def clear_environment(self, config):
        ''' Function prepare environment before new test
        '''
        self.clear_files(config["direcrory"])
        timestamp_file_name = config["job_name"] + "_timestamp.log"
        self.delete_timestamp(timestamp_file_name)    
        
    
#############################################################
# main        
        
if __name__ == '__main__':
    unittest.main()