import time
import os
import wx
import wx._xml
import wx.richtext as rt
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_element_by_xpath(driver, xpath, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )

def get_clickable_element_by_xpath(driver, xpath, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )

class FileItem:
    def __init__(self, path=None, content=None):
        self.path = path
        self.content = content

        if self.path:
            self.type = self.determine_file_type()
        elif self.content:
            self.type = 'text'

    def determine_file_type(self):
        _, ext = os.path.splitext(self.path)
        if ext in ['.jpg', '.png']:
            return 'image'
        elif ext == '.txt':
            return 'text'
        elif ext in ['.mp4']:
            return 'video'
        else:
            return 'unknown'

    def __str__(self):
        return self.path or self.content

    def count_image_types(file_items):
        return sum(1 for item in file_items if item.type == "image")

class PostApp(wx.Frame):
    def __init__(self, parent, title):
        super(PostApp, self).__init__(parent, title=title, size=(800, 550))
        self.file_list = []
        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):
        panel = wx.Panel(self)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        leftvbox = wx.BoxSizer(wx.VERTICAL)
        rightvbox = wx.BoxSizer(wx.VERTICAL)

        login_check_hbox = wx.BoxSizer(wx.HORIZONTAL)

        nickName_label = wx.StaticText(panel, label="닉네임(Id)")

        login_check_hbox.Add(nickName_label, flag=wx.LEFT, border=10)

        login_check_hbox.AddStretchSpacer(1)

        self.login_check = wx.CheckBox(panel, label="로그인하기")

        self.login_check.Bind(wx.EVT_CHECKBOX, self.on_checkbox_toggle)

        login_check_hbox.Add(self.login_check, flag=wx.RIGHT, border=10)

        leftvbox.Add(login_check_hbox, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=0)

        self.nickName_entry = wx.TextCtrl(panel)
        leftvbox.Add(self.nickName_entry, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        password_input_label = wx.StaticText(panel, label="비밀번호")
        leftvbox.Add(password_input_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.password_input_entry = wx.TextCtrl(panel)
        leftvbox.Add(self.password_input_entry, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        title_input_label = wx.StaticText(panel, label="제목")
        leftvbox.Add(title_input_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.title_input_entry = wx.TextCtrl(panel)
        leftvbox.Add(self.title_input_entry, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        upload_btn = wx.Button(panel, label="이미지 업로드")
        upload_btn.Bind(wx.EVT_BUTTON, self.upload_image)

        leftvbox.Add(upload_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.video_upload_btn = wx.Button(panel, label="비디오 업로드")
        self.video_upload_btn.Bind(wx.EVT_BUTTON, self.upload_video)
        self.video_upload_btn.Disable()

        leftvbox.Add(self.video_upload_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        load_btn = wx.Button(panel, label="txt 파일 업로드")
        load_btn.Bind(wx.EVT_BUTTON, self.load_file)

        leftvbox.Add(load_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # 이미지 목록 박스 추가
        self.file_listbox = wx.ListBox(panel)
        leftvbox.Add(self.file_listbox, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        image_list_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.up_button = wx.Button(panel, label="Up")
        self.down_button = wx.Button(panel, label="Down")
        self.delete_button = wx.Button(panel, label="Delete")

        self.up_button.Bind(wx.EVT_BUTTON, self.on_move_up)
        self.down_button.Bind(wx.EVT_BUTTON, self.on_move_down)
        self.delete_button.Bind(wx.EVT_BUTTON, self.on_delete_selected)

        image_list_hbox.Add(self.up_button, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, border=3)
        image_list_hbox.Add(self.down_button, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, border=3)
        image_list_hbox.Add(self.delete_button, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, border=3)

        leftvbox.Add(image_list_hbox, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        left_header_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.center_checkbox = wx.CheckBox(panel, label="중앙 정렬")
        left_header_hbox.Add(self.center_checkbox, proportion=1,
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.font_weight_checkbox = wx.CheckBox(panel, label="굵게 쓰기")
        left_header_hbox.Add(self.font_weight_checkbox, proportion=1,
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        font_size_label = wx.StaticText(panel, label="글자 크기:")
        left_header_hbox.Add(font_size_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.sample_choice = wx.Choice(panel,
                                       choices=["8px", "9px", "10px", "11px", "12px", "14px", "18px", "24px", "36px"])
        left_header_hbox.Add(self.sample_choice, proportion=1,
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        leftvbox.Add(left_header_hbox, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)

        upload_btn = wx.Button(panel, label="글 업로드")
        upload_btn.Bind(wx.EVT_BUTTON, self.upload_content)
        leftvbox.Add(upload_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.text_widget = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        leftvbox.Add(self.text_widget,  proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.run_btn = wx.Button(panel, label="실행")
        self.run_btn.Bind(wx.EVT_BUTTON, self.run_thread)
        rightvbox.Add(self.run_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #갤러라 목록 업로드
        url_load_btn = wx.Button(panel, label="갤러리 목록 업로드(.txt)")
        url_load_btn.Bind(wx.EVT_BUTTON, self.on_load)
        rightvbox.Add(url_load_btn, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.url_text_widget = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        rightvbox.Add(self.url_text_widget, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        log_label = wx.StaticText(panel, label="작업 기록")
        rightvbox.Add(log_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.log_text_widget = rt.RichTextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        rightvbox.Add(self.log_text_widget,  proportion=1,flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox.Add(leftvbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        hbox.Add(rightvbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.nickName_entry.Bind(wx.EVT_TEXT, self.on_text_changed)
        self.password_input_entry.Bind(wx.EVT_TEXT, self.on_text_changed)
        self.title_input_entry.Bind(wx.EVT_TEXT, self.on_text_changed)
        self.text_widget.Bind(wx.EVT_TEXT, self.on_text_changed)
        self.url_text_widget.Bind(wx.EVT_TEXT, self.on_text_changed)
        self.on_text_changed(None)

        panel.SetSizer(hbox)

    def add_file(self, path):
        file_item = FileItem(path=path)
        self.file_list.append(file_item)

    def add_txt_file(self, content):
        file_item = FileItem(content=content)
        self.file_list.append(file_item)

    def append_log(self, message):
        if '[ERROR]' in message:
            color = wx.RED
        elif '[SUCCESS]' in message:
            color = wx.GREEN
        else:
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_text_widget.BeginTextColour(color)  # 텍스트 색상 시작
        self.log_text_widget.WriteText("[" + current_time + "]"+ message + "\n")
        self.log_text_widget.EndTextColour()  # 텍스트 색상 종료
        self.log_text_widget.ShowPosition(self.log_text_widget.GetLastPosition())

    def upload_web_texts(self, driver, content):
        iframe = driver.find_element(By.ID, "tx_canvas_wysiwyg")
        driver.switch_to.frame(iframe)
        content_element = get_element_by_xpath(driver, '/html/body')
        content_element.send_keys(content)

        driver.switch_to.default_content()

    def upload_web_images(self, driver, file_item, mine_type):
        # "사진" 링크를 클릭
        popup_url = "https://gall.dcinside.com/upload/image"
        apply_xpath = '/html/body/div[1]/div/div[2]/button'

        if mine_type == 'image':
            print('print')
            photo_link = get_element_by_xpath(driver, '//*[@id="tx_image"]/a')
            photo_link.click()
            print('print2')

        elif mine_type == 'video':
            vidio_link = get_element_by_xpath(driver, '//*[@id="tx_movie"]/a')
            vidio_link.click()
            popup_url = "https://gall.dcinside.com/upload/movie"
            apply_xpath = '//*[@id="movie_tmp"]/div/div[3]/button'

        # 팝업 창으로 전환
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if driver.current_url == popup_url:
                break

        # self.file_list 내의 이미지 경로만 추출
        file_path = file_item.path
        if not file_path:
            print("No File to upload.")
            return
        file_input = driver.find_element(By.XPATH, '//input[@type="file"]')

        file_input.send_keys(file_path)

        try:
            if mine_type == 'video':
                get_element_by_xpath(driver, '//*[@id="movie_tmp"]/div/div[2]/div[1]/div[1]/img', timeout=50)
            elif mine_type == 'image':
                get_element_by_xpath(driver, '//*[@id="sortable"]/li[1]/img', timeout=10)
        except:
            wx.CallAfter(self.append_log, '파일 업로드 실패')

        apply_element = get_element_by_xpath(driver, apply_xpath)

        apply_element.click()

        # 원래의 메인 창으로 다시 전환
        driver.switch_to.window(driver.window_handles[0])

    def on_text_changed(self, event):
        # 필요한 값 입력 확인
        if (self.nickName_entry.GetValue().strip() and
                self.password_input_entry.GetValue().strip() and
                self.title_input_entry.GetValue().strip() and
                self.url_text_widget.GetValue().strip() and
                len(self.url_text_widget.GetValue().split('\n')) > 0):
            self.run_btn.Enable()  # Run 버튼 활성화
        else:
            self.run_btn.Disable()  # Run 버튼 비활성화

    def on_checkbox_toggle(self, event):
        if self.login_check.IsChecked():
            self.video_upload_btn.Enable()
        else:
            self.video_upload_btn.Disable()

    def post_content(self, driver):

        nickName = self.nickName_entry.GetValue()
        password = self.password_input_entry.GetValue()
        title = self.title_input_entry.GetValue()
        content = self.text_widget.GetValue()
        font_weight_element_xpath = "/html/body/div[2]/main/section/article[2]/form/div[3]/div/div[2]/div/ul[3]/li[1]/div/a"
        font_size_list_element_xpath = "/html/body/div[2]/main/section/article[2]/form/div[3]/div/div[2]/div/ul[2]/li/div[1]/a"
        apply_button_xpath = '//*[@id="write"]/div[5]/button[2]'
        # 글쓰기 버튼
        element = get_clickable_element_by_xpath(driver, '/html/body/div[2]/div[3]/main/section[1]/article[2]/div[3]/div[2]/button')
        # 요소 클릭
        try:
            time.sleep(1)
            element.click()
        except Exception as e:
            print(f"Error during click: {e}")

        if not self.login_check.IsChecked():
            gall_nick_name_element = get_element_by_xpath(driver,'/html/body/div[2]/main/section/article[2]/form/div[1]/fieldset/div[1]/input[1]')
            # input 태그의 value 속성 값 가져오기
            input_value = gall_nick_name_element.get_attribute("value")
            # 값이 있다면 btn_gall_nick_name_x 클릭

            if input_value.strip():  # 값이 비어있지 않은 경우
                btn_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '/html/body/div[2]/main/section/article[2]/form/div[1]/fieldset/div[1]/button[1]'))
                )
                btn_element.click()

            nick_name_element = get_element_by_xpath(driver,
                                                     '/html/body/div[2]/main/section/article[2]/form/div[1]/fieldset/div[1]/input[2]')

            nick_name_element.send_keys(nickName)

            password_element = get_element_by_xpath(driver,
                                                    '/html/body/div[2]/main/section/article[2]/form/div[1]/fieldset/div[2]/input')

            password_element.send_keys(password)

            title_element = get_element_by_xpath(driver, '/html/body/div[2]/main/section/article[2]/form/div[1]/fieldset/div[3]/input')

            title_element.send_keys(title)

        else:
           login_title_element = get_element_by_xpath(driver, '//*[@id="subject"]')
           login_title_element.send_keys(title)
           #xpath update
           font_weight_element_xpath = "/html/body/div[2]/main/section/article[2]/form/div[4]/div/div[2]/div/ul[3]/li[1]/div/a"
           font_size_list_element_xpath = "/html/body/div[2]/main/section/article[2]/form/div[4]/div/div[2]/div/ul[2]/li/div[1]/a"
           apply_button_xpath = "/html/body/div[2]/main/section/article[2]/form/div[6]/button[2]"

        # 이미지 업로드
        if self.font_weight_checkbox.IsChecked():
            font_weight_element = get_element_by_xpath(driver, font_weight_element_xpath)
            font_weight_element.click()

        font_size_list_element = get_element_by_xpath(driver, font_size_list_element_xpath)
        font_size_list_element.click()

        selected_size = self.sample_choice.GetStringSelection()

        size_to_xpath = {
            '8px': '//*[@id="tx_fontsize_menu"]/ul/li[1]/a',
            '9px': '//*[@id="tx_fontsize_menu"]/ul/li[2]/a',
            '10px': '//*[@id="tx_fontsize_menu"]/ul/li[3]/a',
            '11px': '//*[@id="tx_fontsize_menu"]/ul/li[4]/a',
            '12px': '//*[@id="tx_fontsize_menu"]/ul/li[5]/a',
            '14px': '//*[@id="tx_fontsize_menu"]/ul/li[6]/a',
            '18px': '//*[@id="tx_fontsize_menu"]/ul/li[7]/a',
            '24px': '//*[@id="tx_fontsize_menu"]/ul/li[8]/a',
            '36px': '//*[@id="tx_fontsize_menu"]/ul/li[9]/a'
        }

        if selected_size:
            font_size_element = get_element_by_xpath(driver, size_to_xpath[selected_size])
            font_size_element.click()

        if len(self.file_list) > 0:
            for file_item in self.file_list:
                if file_item.type == "image":
                    print("이미지 처리중")
                    self.upload_web_images(driver, file_item, 'image')
                elif file_item.type == "text":
                    print("텍스트 처리중")
                    self.upload_web_texts(driver, file_item.content)  # content를 인자로 전달하도록 수정될 수 있습니다.
                elif file_item.type == "video":
                    print("동영상 처리중")
                    self.upload_web_images(driver, file_item, 'video')
                else:
                    wx.CallAfter(self.append_log, f"알 수 없는 파일 유형: {file_item.path}")
                    print(f"알 수 없는 파일 유형: {file_item.path}")

        #포스팅 내용
        iframe = driver.find_element(By.ID, "tx_canvas_wysiwyg")
        driver.switch_to.frame(iframe)

        if self.center_checkbox.IsChecked():
            image_elements = driver.find_elements(By.CSS_SELECTOR, 'img.txc-image')

            for img in image_elements:
                driver.execute_script("""
                    arguments[0].parentNode.style.textAlign = 'center';
                """, img)

            video_elements = driver.find_elements(By.CSS_SELECTOR, 'video_inbox dc_movie_thumbox')

            for video in video_elements:
                driver.execute_script("""
                    arguments[0].parentNode.style.textAlign = 'center';
                """, video)

            p_elements = driver.find_elements(By.TAG_NAME, 'p')

            for p in p_elements:
                driver.execute_script("""
                    arguments[0].style.textAlign = 'center';
                """, p)

        driver.switch_to.default_content()

        # time.sleep(50)

        apply_button = get_element_by_xpath(driver, apply_button_xpath)
        apply_button.click()
        time.sleep(3)
        # current_url = driver.current_url
        # wait = WebDriverWait(driver, 30)
        # wait.until(EC.url_changes(current_url))
        # time.sleep(100)


    def run_post_board(self):
        # 웹드라이버 초기화
        # options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # driver = webdriver.Chrome(options=options)
        driver = webdriver.Chrome()

        driver.get("https://gall.dcinside.com/")

        self.append_log("Start")

        try:
            if self.login_check.IsChecked():
                login_button_element = get_clickable_element_by_xpath(driver,
                                                                      '/html/body/div[2]/header/div/div[2]/ul/li[10]/a')
                login_button_element.click()

                login_id_input_element = get_element_by_xpath(driver,
                                                              '/html/body/div[2]/main/div/article/section/div/div[1]/div/form/fieldset/div[1]/input[1]')

                login_id_input_element.send_keys(self.nickName_entry.GetValue())

                login_password_input_element = get_element_by_xpath(driver,
                                                                    '/html/body/div[2]/main/div/article/section/div/div[1]/div/form/fieldset/div[1]/input[2]')
                login_password_input_element.send_keys(self.password_input_entry.GetValue())

                login_submit_btn = get_clickable_element_by_xpath(driver,
                                                                  '/html/body/div[2]/main/div/article/section/div/div[1]/div/form/fieldset/button')
                current_url = driver.current_url

                login_submit_btn.click()
                wait = WebDriverWait(driver, 3)
                wait.until(EC.url_changes(current_url))
        except:
            wx.CallAfter(self.append_log, f"[ERROR] 로그인에 실패하였습니다")
            driver.quit()
            return

        matching_links = {}
        for data in self.data_list:
            if not data:
                break
            try:
                a_element = driver.find_element(By.XPATH, f"//li/a[text()='{data}']")
                matching_links[data] = a_element.get_attribute('href')
            except:
                wx.CallAfter(self.append_log, f"[ERROR] {data} 갤러리를 찾을 수 없습니다.")

        if not matching_links:
            wx.CallAfter(self.append_log, "[ERROR] 아무 갤러리도 찾을 수 없습니다")
            driver.quit()
            return

        for link_text, link_url in matching_links.items():
            wx.CallAfter(self.append_log, f"{link_text} 갤러리 접속...")
            # self.append_log(f"{link_text} 갤러리 접속...")
            driver.get(link_url)
            try:
                self.post_content(driver)
                wx.CallAfter(self.append_log, f"[SUCCESS] {link_text} 갤러리 업로드 성공")
                # self.append_log(f"[SUCCESS] {link_text} 갤러리 업로드 성공")
            except:
                wx.CallAfter(self.append_log, f"[ERROR] {link_text} 갤러리 업로드 실패")
                # self.append_log(f"[ERROR] {link_text} 갤러리 업로드 실패")

        driver.quit()

    def run_thread(self, event):
        thread = threading.Thread(target=self.run_post_board)
        thread.start()
    def load_file(self, event):
        filepath = wx.FileDialog(self, "Open TXT file", wildcard="TXT files (*.txt)|*.txt", style=wx.FD_OPEN)
        if filepath.ShowModal() == wx.ID_OK:
            with open(filepath.GetPath(), 'r') as file:
                content = file.read()
                self.add_txt_file(content)
                if len(content) > 8:
                    extracted_string = content[:8] + "..."
                else:
                    extracted_string = content
                self.file_listbox.Append(extracted_string)
                # content = file.read()
                # self.text_widget.SetValue(content)
        filepath.Destroy()

    def upload_content(self, event):
        content = self.text_widget.GetValue()

        if content:
            file_item = FileItem(content=content)
            self.file_list.append(file_item)
            if len(content) > 8:
                extracted_string = content[:8] + "..."
            else:
                extracted_string = content
            self.file_listbox.Append(extracted_string)

        self.text_widget.SetValue('')

    def on_load(self, event):
        filepath = wx.FileDialog(self, "Open TXT file", wildcard="TXT files (*.txt)|*.txt", style=wx.FD_OPEN)
        if filepath.ShowModal() == wx.ID_OK:
            with open(filepath.GetPath(), 'r', encoding='utf-8') as file:
                self.data_list = file.read().split('\n')
                self.url_text_widget.SetValue('\n'.join(self.data_list))

    def upload_image(self, event):
        filepath = wx.FileDialog(self, "Open Image file", wildcard="Image files (*.jpg;*.png)|*.jpg;*.png", style=wx.FD_OPEN)
        if filepath.ShowModal() == wx.ID_OK:
            # 선택한 이미지의 경로를 리스트에 추가
            self.add_file(filepath.GetPath())
            # self.image_list.append(filepath.GetPath())
            # 이제 ListBox에도 업로드된 이미지의 경로를 추가
            self.file_listbox.Append(filepath.GetPath())
        filepath.Destroy()

    def upload_video(self, event):
        filepath = wx.FileDialog(self,
                                 "Open Video file",
                                 wildcard="Video files (*.mp4;*.avi;*.mov;*.webm)|*.mp4;*.avi;*.mov;*.webm",
                                 style=wx.FD_OPEN)
        if filepath.ShowModal() == wx.ID_OK:
            self.add_file(filepath.GetPath())
            self.file_listbox.Append(filepath.GetPath())
        filepath.Destroy()

    def on_move_up(self, event):
        selection = self.file_listbox.GetSelection()
        if selection > 0:
            current_label = self.file_listbox.GetString(selection)
            self.file_listbox.Delete(selection)
            self.file_listbox.Insert(current_label, selection - 1)
            self.file_listbox.SetSelection(selection - 1)
            self.file_list[selection], self.file_list[selection-1] = self.file_list[selection-1], self.file_list[selection]

    def on_move_down(self, event):
        selection = self.file_listbox.GetSelection()
        if selection < (self.file_listbox.GetCount() - 1) and selection != wx.NOT_FOUND:
            current_label = self.file_listbox.GetString(selection)
            self.file_listbox.Delete(selection)
            self.file_listbox.Insert(current_label, selection + 1)
            self.file_listbox.SetSelection(selection + 1)

            self.file_list[selection], self.file_list[selection + 1] = self.file_list[selection + 1], \
            self.file_list[selection]

    def on_delete_selected(self, event):
        selection = self.file_listbox.GetSelection()
        if selection != wx.NOT_FOUND:
            self.file_listbox.Delete(selection)
            del self.file_list[selection]

app = wx.App()
PostApp(None, title="Post")
app.MainLoop()