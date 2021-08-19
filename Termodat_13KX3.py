import atomize.device_modules.Termodat_13KX3 as tcterm
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtGui import QPixmap
import pyqtgraph as pg
import serial
import sys
import datetime
from calendar import monthrange # To know how many days in current month
class MyThread(QtCore.QThread):
    mysignal_temp_ch1 = QtCore.pyqtSignal(str)
    mysignal_temp_ch2 = QtCore.pyqtSignal(str)
    mysignal_record_new_parameters = QtCore.pyqtSignal()
     
    def __init__ (self, parent=None,update_time=7):
        self.updatetime = update_time
        QtCore.QThread.__init__(self,parent)
        
    def run(self):
        while True:
            self.sleep(self.updatetime)
            text_temp_ch1 = ( tc.tc_temperature('1') )
            text_temp_ch2 = ( tc.tc_temperature('2') )
            
            self.mysignal_temp_ch1.emit(  "{}".format(text_temp_ch1)    )
            self.mysignal_temp_ch2.emit(  "{}".format(text_temp_ch2)    )
            self.mysignal_record_new_parameters.emit()
                       
class MyWindow(QtWidgets.QWidget):
    def __init__(self,parent= None):
        QtWidgets.QWidget.__init__(self,parent)
        self.nowtime = datetime.datetime.now() #Current date and time  
        (self.newtime_year, self.newtime_month, self.newtime_day, self.newtime_hour, self.newtime_minute,self.newtime_second)   = (self.nowtime.year, self.nowtime.month , self.nowtime.day , self.nowtime.hour, self.nowtime.minute,self.nowtime.second)  
        self.updatetime= 5
        global tc
        tc = tcterm.Termodat_13KX3()
        tc.tc_sensor('1','On')
        self.max_temp_ch1 = 26
        self.currenttemp_ch1 = ( tc.tc_temperature('1') )    
        self.currenttemp_ch2 = ( tc.tc_temperature('2') ) 
        self.Xtime = {0:'0'}
        self.Ytemp_ch1 = []   
        self.Ytemp_ch2 = []
        
        path = ('//home/arkan//ITC//Clever_system_for_crystals_at_magnet//text_date' + '//' + str(self.nowtime.day) +'_' + str(self.nowtime.month)+ '_' + str(self.nowtime.year) + '_temp_date.txt')
        self.fch = open( path, "a+"  ) #file where new temperature and time of this temperature will be written
        
        self.design_window = uic.loadUi('//home//arkan//ITC//Clever_system_for_crystals_at_magnet//First_programs//Window_1.ui', self)
        self.change_window()
                                            #Attributes newtempold and speedold will be compared with new ones in the method "record_new_parameters". If new and old are different the parameters will be changed
        self.newtempold = float(tc.tc_setpoint('1') )           
                                            #Set the first date for parametrers of window
        self.design_window.newtempEdit.setPlainText(str (self.newtempold)  )
        if tc.tc_speed_state('1') == 'Off':
            self.design_window.speedEdit.setPlainText('Off')
            self.speedold = "Off"
        else:
            self.speedold = (tc.tc_setspeed('1') )
            self.design_window.speedEdit.setPlainText(str (self.speedold)  )
        self.Xtime[0] = (str(self.nowtime.hour) + ':' + str(self.nowtime.minute) + ':'+ str(self.nowtime.second) )
                                            #End setting
                                            
        DateTime = QtCore.QDateTime(int(self.newtime_year), int(self.newtime_month), int(self.newtime_day), int(self.newtime_hour), int(self.newtime_minute), int(self.newtime_second) )  
        self.design_window.dateTimeEdit.setDateTime(DateTime )
        
        self.update_XandYdata()
        self.draw_graphs()
        self.write_txts()
        self.draw_LOGO()
        
        self.mythread = MyThread(update_time=self.updatetime)
        self.mythread.start() 
        self.mythread.started.connect(self.start_thread)
        self.mythread.finished.connect(self.finish_thread)
        
        self.mythread.mysignal_temp_ch1.connect(self.update_temp_ch1, QtCore.Qt.QueuedConnection)
        self.mythread.mysignal_temp_ch2.connect(self.update_temp_ch2, QtCore.Qt.QueuedConnection)
        self.mythread.mysignal_record_new_parameters.connect(self.record_new_parameters, QtCore.Qt.QueuedConnection)
    def check_overheat(self):
        if float(self.currenttemp_ch1) >= self.max_temp_ch1:
            if tc.tc_sensor('1') == 'On':
                tc.tc_sensor('1', 'Off')
        else:
            if tc.tc_sensor('1') == 'Off':
                tc.tc_sensor('1', 'On')       
                    
    def show_information(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.about(self, "Title", "Message")
    def draw_LOGO(self):
        pix = QPixmap('//home/arkan//ITC//Clever_system_for_crystals_at_magnet//ITC.jpeg')
        Qsize = self.design_window.LOGO_graphicsView.size()
        height = int( Qsize.height() )
        width= int( Qsize.width() )
        pix.scaled(width, height)
        item = QtWidgets.QGraphicsPixmapItem(pix)     
        scene = QtWidgets.QGraphicsScene(self.design_window.LOGO_graphicsView)
        scene.addItem(item)
        self.design_window.LOGO_graphicsView.setScene(scene)
    def change_window(self):
        self.design_window.mistakesEdit.setStyleSheet("color: rgb(255, 0, 0);")
    def write_txts(self):
        if self.nowtime.hour == 0 and self.nowtime.minute == 0 and self.nowtime.second <=self.updatetime:
            self.fch.close()
            path = ('//home/arkan//ITC//Clever_system_for_crystals_at_magnet//text_date' + '\\' + str(self.nowtime.day) +'_' + str(self.nowtime.month)+ '_' + str(self.nowtime.year) + '_temp_date.txt')
            self.fch = open( path, "a+"  ) #file where new temperature and time of this temperature will be written
        self.fch.write( str (self.Xtime[len(self.Ytemp_ch1) -1] )  + "    " + str (self.Ytemp_ch1[len(self.Ytemp_ch1) -1 ]  ) + "    " + str (self.Ytemp_ch2[len(self.Ytemp_ch2) -1 ]  )  +'\n')
    def update_XandYdata(self):
        flag_number = int(12*60*60/self.updatetime)
        
        sizeY_ch1 = len(self.Ytemp_ch1)
        sizeY_ch2= len(self.Ytemp_ch2)
        if sizeY_ch1 <= flag_number:
            self.Ytemp_ch1.append(self.currenttemp_ch1)
            self.Xtime[len(self.Ytemp_ch1) -1] = (str(self.nowtime.hour) + ':' + str(self.nowtime.minute) + ':'+ str(self.nowtime.second) )
        else:
            for i in range(sizeY_ch1-1):
                self.Ytemp_ch1[i] = self.Ytemp_ch1[i+1]
                self.Xtime[i] = self.Xtime[i+1]
            self.Ytemp_ch1[sizeY_ch1-1] = self.currenttemp_ch1
            self.Xtime[sizeY_ch1-1] = (str(self.nowtime.hour) + ':' + str(self.nowtime.minute) + ':'+ str(self.nowtime.second) )
        
        if sizeY_ch2 <= flag_number:
            self.Ytemp_ch2.append(self.currenttemp_ch2)
            self.Xtime[len(self.Ytemp_ch2) -1] = (str(self.nowtime.hour) + ':' + str(self.nowtime.minute) + ':'+ str(self.nowtime.second) )
        else:
            for i in range(sizeY_ch2-1):
                self.Ytemp_ch2[i] = self.Ytemp_ch2[i+1]
                self.Xtime[i] = self.Xtime[i+1]
            self.Ytemp_ch2[sizeY_ch2-1] = self.currenttemp_ch1
            self.Xtime[sizeY_ch2-1] = (str(self.nowtime.hour) + ':' + str(self.nowtime.minute) + ':'+ str(self.nowtime.second) )
    def draw_graphs(self):
        Xticks = {0:''}
        if (len(self.Ytemp_ch1) >=6):
            for i in range(6):
                Xticks[int( (len(self.Ytemp_ch1)-1)* i/5 ) ] = self.Xtime[int( (len(self.Ytemp_ch1)-1)* (i)/5) ]
        else:
            Xticks = self.Xtime
        stringaxis_ch1 = pg.AxisItem(orientation='bottom')
        stringaxis_ch1.setTicks([ Xticks.items()])
        
        Plt_ch1 = pg.PlotWidget(axisItems={'bottom': stringaxis_ch1})  #Or pg.PlotItem()
        Qsize = self.design_window.graphicsView_ch1.size()
        height_ch1 = int( 0.95*Qsize.height() )
        width_ch1= int( 0.98*Qsize.width() )
        Plt_ch1.resize(width_ch1, height_ch1)
        
        Plt_ch1.plot(list( self.Xtime.keys()),self.Ytemp_ch1,clear=True)
        
        scene_ch1 = QtWidgets.QGraphicsScene()
        scene_ch1.addWidget(Plt_ch1)   #Or pg.addItem()
        self.design_window.graphicsView_ch1.setScene(scene_ch1)
               
        stringaxis_ch2 = pg.AxisItem(orientation='bottom')
        stringaxis_ch2.setTicks([ Xticks.items()])       
                  
        Plt_ch2 = pg.PlotWidget(axisItems={'bottom': stringaxis_ch2})  #Or pg.PlotItem()
        Qsize = self.design_window.graphicsView_ch2.size()
        height_ch2 = int( 0.95*Qsize.height() )
        width_ch2= int( 0.98*Qsize.width() )
        Plt_ch2.resize(width_ch2, height_ch2)
        
        Plt_ch2.plot(list( self.Xtime.keys()),self.Ytemp_ch2,clear=True)
        
        scene_ch2 = QtWidgets.QGraphicsScene()
        scene_ch2.addWidget(Plt_ch2)   #Or pg.addItem()
        self.design_window.graphicsView_ch2.setScene(scene_ch2)
        
    def start_thread(self):
        pass
        
    def finish_thread(self):
        pass
        
    def update_temp_ch1(self,text):
        self.design_window.ch1_temp.display(text)
        self.currenttemp_ch1 = float(text)
    def update_temp_ch2(self,text):
        self.design_window.ch2_temp.display(text)    
        self.currenttemp_ch2 = float(text)
    def set_time(self):
        if type(self.newtempold) == str:
            return (1, 1, 1, 1, 1,1)
        elif type(self.speedold)==str:
            return (int(self.nowtime.year), int(self.nowtime.month), int(self.nowtime.day), int(self.nowtime.hour), int(self.nowtime.minute), int(self.nowtime.second))
        else:
            current_temp = tc.tc_temperature('1')
            delta_time = abs(  (self.newtempold - current_temp)/int(self.speedold)  )
            delta_hour = int(delta_time )
            delta_minute = int ( (delta_time -  delta_hour) * 60 )
        
            self.newtime_hour = self.nowtime.hour + delta_hour
            self.newtime_minute = self.nowtime.minute + delta_minute
            self.newtime_second = self.nowtime.second
            self.newtime_day = self.nowtime.day
            self.newtime_month = self.nowtime.month
            self.newtime_year = self.nowtime.year
            while (   ( self.newtime_hour>=24 )or (self.newtime_minute>=60) or self.newtime_day >=( monthrange(self.newtime_year, self.newtime_month) ) [1] ) :
                if self.newtime_minute >=60:
                    self.newtime_minute = self.newtime_minute -60
                    self.newtime_hour = self.newtime_hour + 1
                if self.newtime_hour >=24:
                    self.newtime_hour = self.newtime_hour -24
                    self.newtime_day = self.newtime_day + 1
                if self.newtime_day >=( monthrange(self.newtime_year, self.newtime_month) )[1]:
                    self.newtime_day = self.newtime_day - ( monthrange(self.newtime_year, self.newtime_month) )[1]
                    self.newtime_month = self.newtime_month +1    
                if self.newtime_month >=12:
                    self.newtime_month = self.newtime_month -12
                    self.newtime_year = self.newtime_year + 1
            return (self.newtime_year, self.newtime_month, self.newtime_day, self.newtime_hour, self.newtime_minute, self.newtime_second)
           
    def record_new_parameters(self):
                #Set new temperature
        self.nowtime = datetime.datetime.now() #Current date and time  
        mistake_flag = 0  # If in the end of setting parameters mistake_flag == 0 then there are no mistakes.
        newtemp = self.design_window.newtempEdit.toPlainText()
        try:
            newtemp = float(newtemp)
            if newtemp!=self.newtempold:
                tc.tc_setpoint('1',newtemp)
                self.newtempold = newtemp         
        except Exception as ex:
            if (type(ex) == ValueError):
                self.newtempold = "Wrong"
                self.design_window.mistakesEdit.setPlainText('Wrong the new temperature.The new temperature is a number from 8 to room temperature in degree of Celsium. Try another time')
                mistake_flag = 1
            elif (type(ex) == tcterm.TermodatError):
                self.newtempold = "Wrong"
                self.design_window.mistakesEdit.setPlainText(str(ex))
                mistake_flag = 1
            elif (str(type(ex)) == 'SerialException'):
                    self.design_window.mistakesEdit.setPlainText(str(ex))
                    mistake_flag = 1
            else:
                sys.exit()
                    #Set new speed
        speed = self.design_window.speedEdit.toPlainText()        
    
        if speed != "Off":
            try:
                speed = float(speed)
                if speed!=self.speedold:
                    if speed == 0:
                        tc.tc_speed_state('1',"Off")    
                        self.speedold = 'Off'   
                        self.design_window.speedEdit.setPlainText(self.speedold)     
                    else:
                        if (speed- int(speed)) !=0:
                            speed = int(speed) + 1
                            self.speedold = (speed)
                            self.design_window.speedEdit.setPlainText(str(speed)) 
                        tc.tc_speed_state('1',"On")   
                        tc.tc_setspeed('1', speed)
                        self.speedold = speed
            except Exception as ex:
                if (type(ex) == ValueError):
                    self.speedold = "Wrong"
                    self.design_window.mistakesEdit.setPlainText('Wrong speed. The speed is a integer number from 1 to 1000 degrees/hour. Try another time')
                    mistake_flag = 1
                elif (type(ex) == tcterm.TermodatError):
                    self.speedold = "Wrong"
                    self.design_window.mistakesEdit.setPlainText(str(ex))
                    mistake_flag = 1
                elif ( str(type(ex) ) == 'SerialException'):
                    self.design_window.mistakesEdit.setPlainText(str(ex))
                    mistake_flag = 1
                else:
                    sys.exit()
        else:
            self.speedold = "Off"  
        if mistake_flag ==0:
            self.design_window.mistakesEdit.setPlainText('There are no mistakes!')
            
        DateTime = self.set_time( )  
        DateTime = QtCore.QDateTime(*DateTime)  
        self.design_window.dateTimeEdit.setDateTime(DateTime )
        
        self.update_XandYdata()
        self.draw_graphs()  
        self.write_txts()
        self.check_overheat()
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    NewWindow = MyWindow()
    window = NewWindow.design_window
    window.show()
    sys.exit(app.exec_())

    
if __name__ == "__main__":
    main()
