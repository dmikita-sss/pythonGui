import pandas as pd
import numpy as numpy
from utils.logger import LoggerObj
import sys
import os
import requests
import tkinter
from datetime import datetime
import boto3
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter.ttk import *
import threading
from tkinter import messagebox
from tkinter import filedialog
from tkinter import Button,ttk,StringVar
from selenium import webdriver
from functools import partial 
import configparser


root= tkinter.Tk()
BUTTON_LABEL_REFERENCE='参照'
EXECUTE_LIST=['ファイル取得','ファイル削除']
class PythonGui():

    lock = threading.Lock()

    inputFileName=StringVar()
    inputval=StringVar()

    inputFolder=StringVar()
    outputFolder=StringVar()

    progressMsg=StringVar()
    progressBar=None
    progressMsgBox=None

    progressStatusBar=None
    progressValue=None

    def init(self):
        self.iniFile=configparser.ConfigParser()
        self.iniFile.read("resources/appConfig.ini","UTF-8")
    
    # 初期設定後の動作
    def preparation(self,logfilename):
        self._executer=partial(self.execute,logfilename)

    def progressSequence(self,msg,sequenceValue=0):
        self.progressMsg.set(msg)
        self.progressValue=self.progressValue+sequenceValue
        self.progressStatusBar.configure(value=self.progressValue)

    def quite(self):
        if messagebox.askokcancel('終了確認','処理を終了しますか？'):
            if self.lock.acquire(blocking=FALSE):
                pass
            else:
                messagebox.showinfo('終了確認','処理起動中はブラウザを閉じてください。')
            self.lock.release()
            root.quit()
        else:
            pass

    def execute(self,logfilename):

        logObj=LoggerObj()
        log=logObj.createLog(logfilename)
        log.info('処理開始')
        # driver=webdriver.Chrome('C:/webdrivers/chromedriver.exe')
        # driver.get('http://example.selenium.jp/reserveApp/')

        aws_access_key_id=self.iniFile.get('aws','aws_access_key_id')
        aws_secret_access_key_id=self.iniFile.get('aws','aws_secret_access_key_id')
        if aws_access_key_id =='':
            s3 = boto3.resource('s3')
            s3client=boto3.client('s3')
        else:
            s3 = boto3.resource('s3',
                                                aws_access_key_id=aws_access_key_id,
                                                aws_secret_access_key=aws_secret_access_key_id)
            s3client=boto3.client('s3', 
                                                aws_access_key_id=aws_access_key_id,
                                                aws_secret_access_key=aws_secret_access_key_id)

        bucketName=self.inputFileName.get()
        resultFolder=self.outputFolder.get()
        dataBaseDir=os.path.join(resultFolder,bucketName)

        executeType=EXECUTE_LIST.index(self.combo.get())


        s3bucket=s3.Bucket(bucketName)
        objs = s3bucket.meta.client.list_objects_v2(Bucket=s3bucket.name)

        for o in objs.get('Contents'):
            key = o.get('Key')
            s3Paths=os.path.splitext(key)
            if len(s3Paths[1]) !=0:
                keys=key.split('/')
                filename=keys[len(keys)-1]
                if executeType==0:
                    outputDataDir=key.split(filename)[0]
                    outputDataDir=os.path.join(dataBaseDir,outputDataDir)
                    os.makedirs(outputDataDir,exist_ok=True)
                    outputDataFile=os.path.join(outputDataDir,filename)
                    s3bucket.download_file(key,outputDataFile)
                else:
                    s3client.delete_object(Bucket=s3bucket.name, Key=key)

        self.progressBar.stop()
        self.progressMsgBox.after(10,self.progressSequence('処理完了',sequenceValue=50))
        root.update_idletasks()

        log.info('処理終了')
        self.lock.release()
    

    def doExecute(self):
        if self.lock.acquire(blocking=FALSE):
            if messagebox.askokcancel('実行前確認','処理を実行しますか？'):
                self.progressValue=0
                self.progressStatusBar.configure(value=self.progressValue)
                self.progressBar.configure(maximum=10,value=0)
                self.progressBar.start(100)
                th = threading.Thread(target=self._executer)
                th.start()
            else:
                self.lock.release()
        else:
            messagebox.showwarning('エラー','処理実行中です')


    def progressMsgSet(self,msg):
        self.progressMsg.set(msg)

    def progressStart(self):
        self.progressBar.start(100)

    def inputResultFolderButton(self):
        dirname = filedialog.askdirectory()
        self.outputFolder.set(dirname)
        

    def popUpMsg(self,event):
        tkinter.messagebox.showinfo('inputValue',self.inputval.get())

    def main(self):
        root.title("Python GUI")

        content = ttk.Frame(root)
        frame = ttk.Frame(content,  relief="sunken", width=300, height=500)
        title = ttk.Label(content, text="Python GUI")

        content.grid(column=0, row=0)


        title.grid(column=0, row=0, columnspan=4)

        fileLabel=ttk.Label(content,text="バケット名")
        pulldownLabel=ttk.Label(content,text="処理内容")

        fileInput=ttk.Entry(content,textvariable=self.inputFileName,width=23)
        bucketName=self.iniFile.get('aws','bucketName')
        self.inputFileName.set(bucketName)

        resultFolderLabel=ttk.Label(content,text="フォルダ指定")
        self.outputFolder.set(os.getcwd())
        resultFolderInput=ttk.Entry(content,textvariable=self.outputFolder,width=20)
        resultDirectoryInputButton=ttk.Button(content, text=BUTTON_LABEL_REFERENCE,command=self.inputResultFolderButton)

        # コンボボックスの作成(rootに配置,リストの値を編集不可(readonly)に設定)
        self.combo = ttk.Combobox(content, state='readonly')
        # リストの値を設定
        self.combo["values"] = tuple(EXECUTE_LIST)
        # デフォルトの値を食費(index=0)に設定
        self.combo.current(0)


        labelStyle=ttk.Style()
        labelStyle.configure('PL.TLabel',font=('Helvetica',10,'bold'),background='white',foreground='red')
        self.progressMsgBox=ttk.Label(content,textvariable=self.progressMsg,width=20,style='PL.TLabel')
        self.progressMsg.set('処理待機中')

        self.progressBar=ttk.Progressbar(content,orient=HORIZONTAL,length=140,mode='indeterminate')
        self.progressBar.configure(maximum=10,value=0)

        self.progressStatusBar=ttk.Progressbar(content,orient=HORIZONTAL,length=140,mode='determinate')


        resultDirectoryInputButton=ttk.Button(content, text=BUTTON_LABEL_REFERENCE,command=self.inputResultFolderButton)
         
        executeButton=ttk.Button(content,text='実行',command=self.doExecute)
        quiteButton=ttk.Button(content,text='終了',command=self.quite)

        fileLabel.grid(column=1, row=1,sticky='w')
        fileInput.grid(column=2, row=1)
        pulldownLabel.grid(column=1, row=2,sticky='w')

        resultFolderLabel.grid(column=1, row=5,sticky='w')
        resultFolderInput.grid(column=2, row=5)
        resultDirectoryInputButton.grid(column=3, row=5)

        # コンボボックスの配置
        self.combo.grid(column=2, row=2)
        executeButton.grid(column=1, row=6,columnspan=3,sticky='we')
        # self.progressMsgBox.grid(column=1, row=9,columnspan=2,sticky='we')
        # self.progressBar.grid(column=1, row=10,columnspan=2,sticky='we')
        # self.progressStatusBar.grid(column=1, row=11,columnspan=2,sticky='we')
        quiteButton.grid(column=1, row=7,columnspan=3,sticky='we')
        self.progressMsgBox.grid(column=1, row=8,columnspan=3,sticky='we')




        root.mainloop()



if  __name__ == "__main__":
    pythonGui=PythonGui()
    pythonGui.init()
    pythonGui.preparation('log')
    pythonGui.main()
