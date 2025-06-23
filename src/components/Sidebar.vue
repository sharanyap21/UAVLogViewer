<template>
    <div class="nav-side-menu col-lg-2">
        <div class="sidebar-scroll-container">
            <i class="fa fa-bars fa-2x toggle-btn" v-b-toggle.menucontent></i>
            <b-collapse class="menu-content collapse out" id="menucontent" visible>
                <div class="sidebar-header" v-if="state.file">
                    <button @click="goBack" class="back-button" title="Go back to upload">
                        <i class="fa fa-arrow-left"></i>
                    </button>
                </div>
                <div v-if="state.file" class="button-grid">
                    <button
                        class="grid-button"
                        v-if="state.params"
                        title="Parameters"
                        @click="state.showParams = !state.showParams"
                        :class="{ active: state.showParams }">
                        <i class="fa fa-cogs"></i>
                    </button>
                    <button
                        class="grid-button"
                        title="Radio Sticks"
                        @click="state.showRadio = !state.showRadio"
                        :class="{ active: state.showRadio }">
                        <i class="fa fa-gamepad"></i>
                    </button>
                    <button
                        class="grid-button"
                        title="MagFit Tool"
                        @click="state.showMagfit = !state.showMagfit"
                        :class="{ active: state.showMagfit }">
                        <i class="fa fa-compass"></i>
                    </button>
                    <button
                        class="grid-button"
                        title="EKF Helper"
                        @click="state.showEkfHelper = !state.showEkfHelper"
                        :class="{ active: state.showEkfHelper }">
                        <i class="fa fa-sitemap"></i>
                    </button>
                    <button
                        class="grid-button"
                        title="Messages"
                        v-if="state.textMessages"
                        @click="state.showMessages = !state.showMessages"
                        :class="{ active: state.showMessages }">
                        <i class="fa fa-comment"></i>
                    </button>
                    <button
                        class="grid-button"
                        title="Attitude"
                        @click="state.showAttitude = !state.showAttitude"
                        :class="{ active: state.showAttitude }">
                        <i class="fa fa-plane-departure"></i>
                    </button>
                    <button
                        class="grid-button"
                        title="Record Screen"
                        @click="startCapture"
                        v-if="!recording">
                        <i class="fa fa-play"></i>
                    </button>
                    <button
                        class="grid-button"
                        @click="stopCapture"
                        v-if="recording" :class="{ active: recording }"
                        title="Stop Recording">
                        <i class="fa fa-stop"></i>
                    </button>
                    <button class="grid-button" v-if="this.chunks" @click="download" title="Download Recording">
                        <i class="fa fa-download"></i>
                    </button>
                    <button
                        class="grid-button"
                        v-if="state.logType === 'tlog'"
                        @click="downloadTrimmed"
                        title="Download Trimmed Log">
                        <i class="fa fa-file-download"></i>
                    </button>
                    <button
                        class="grid-button"
                        @click="state.showDeviceIDs = !state.showDeviceIDs"
                        :class="{ active: state.showDeviceIDs }"
                        title="Sensors">
                        <i class="fa fa-microchip"></i>
                    </button>
                    <button
                        class="grid-button"
                        v-if="state.files"
                        @click="toggleFilesList"
                        :class="{ active: showFilesList }"
                        title="Files">
                        <i class="fa fa-file"></i>
                    </button>
                </div>
                <div v-if="state.file" class="text-button-group full-width">
                    <div class="radio-mode-wrapper">
                        <span>Radio Mode</span>
                        <select v-model="state.radioMode">
                            <option value="1">1</option>
                            <option value="2">2</option>
                        </select>
                    </div>
                </div>
                <span v-if="state.file" class="filename">Current file: {{state.file}}</span>
                <div v-if="state.files && showFilesList" class="files-container">
                    <ul class="files-list">
                        <span class="files-header">Files:</span>
                        <li
                            v-for="filename in Object.keys(state.files)"
                            :key="filename"
                            href="#"
                            @click="downloadFile(filename)">
                            <i class="fa fa-file-download"></i>
                            {{ filename }}
                        </li>
                    </ul>
                </div>
                <div v-if="state.file">
                    <plotSetup/>
                    <message-menu/>
                </div>
            </b-collapse>
        </div>
    </div>
</template>

<script>
import MessageMenu from './SideBarMessageMenu.vue'
import { store } from './Globals.js'
import PlotSetup from './PlotSetup.vue'
export default {
    name: 'sidebar',
    data () {
        return {
            state: store,
            chunks: false,
            blob: null,
            recording: false,
            recorder: null,
            stream: null,
            downloadURL: '',
            fileName: 'video.mp4',
            showFilesList: false
        }
    },
    methods: {
        startCapture (displayMediaOptions) {
            navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: 'screen' } })
                .then((stream) => { this.record(stream) })
                .catch(err => { console.error('Error:' + err); return null })
        },
        stopCapture () {
            this.recorder.stop()
            this.stream.getTracks().forEach(track => track.stop())
        },
        record (stream) {
            const recorder = new MediaRecorder(stream)
            const chunks = []
            recorder.ondataavailable = e => chunks.push(e.data)
            this.stream = stream
            this.recorder = recorder
            this.recorder.start()
            this.recording = true
            recorder.onstop = e => {
                const completeBlob = new Blob(chunks, { type: chunks[0].type })
                this.chunks = true
                this.blob = completeBlob
                this.recording = false
            }
        },
        download () { this.$refs.downloadFile.click() },
        downloadTrimmed () { this.$eventHub.$emit('trimFile') },
        createDownloadURL (data, fileName) {
            const a = document.createElement('a')
            a.href = data
            a.download = fileName
            document.body.appendChild(a)
            a.style.display = 'none'
            a.click()
            a.remove()
        },
        downloadBlob (data, fileName, mimeType) {
            const blob = new Blob([data], { type: mimeType })
            const url = window.URL.createObjectURL(blob)
            this.createDownloadURL(url, fileName)
            setTimeout(() => window.URL.revokeObjectURL(url), 1000)
        },
        downloadFile (filename) {
            this.downloadBlob(this.state.files[filename], filename, 'application/octet-stream')
        },
        goBack () { window.location.reload() },
        toggleFilesList () { this.showFilesList = !this.showFilesList }
    },
    created () { this.$eventHub.$on('set-selected', this.setSelected) },
    watch: { blob () { this.downloadURL = URL.createObjectURL(this.blob) } },
    components: { PlotSetup, MessageMenu }
}
</script>

<style scoped>
@media (min-width: 575px) and (max-width: 992px) {
    a {
        padding: 2px 60px 2px 55px;
    }
}
.sidebar-header { margin-bottom: 15px; }
.back-button {
    background: none;
    border: none;
    color: #8E8F95;
    font-size: 16px;
    cursor: pointer;
    padding: 10px;
}
.back-button:hover { color: #fff; }
.back-button i { margin: 0; }
.button-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    margin-bottom: 6px;
    margin-right: 10px;
    margin-left: 10px;
}
.grid-button {
    background-color: #32343F;
    border: none;
    border-radius: 8px;
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background-color 0.2s;
}
.grid-button:hover { background-color: #414352; }
.grid-button.active {
    background-color: #e2601a;
    color: #fff;
}
.grid-button i {
    font-size: 18px;
    color: #E2E2E2;
    margin: 0;
}
.grid-button.active i { color: #fff; }
.text-button-group.full-width {
    width: calc(100% - 20px);
    display: flex;
    gap: 10px;
    margin-bottom: 2px;
    margin-left: 10px;
    margin-right: 0;
}
.text-button,
.radio-mode-wrapper {
    flex: 1 1 0;
    min-width: 0;
    box-sizing: border-box;
    height: 45px;
    justify-content: center;
    align-items: center;
    display: flex;
}
.text-button {
    background-color: #32343F;
    border: none;
    border-radius: 8px;
    padding: 10px;
    color: #E2E2E2;
    font-size: 14px;
    font-weight: 500;
    text-align: center;
    cursor: pointer;
    transition: background-color 0.2s;
    white-space: nowrap;
}
.text-button:hover, .radio-mode-wrapper:hover { background-color: #414352; }
.text-button.active {
    background-color: #424866;
    color: #fff;
}
.radio-mode-wrapper {
    background-color: #32343F;
    border: none;
    border-radius: 8px;
    padding: 10px 12px;
    color: #E2E2E2;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    white-space: nowrap;
}
.radio-mode-wrapper select {
    background: transparent;
    color: #E2E2E2;
    border: none;
    border-radius: 5px;
    padding: 4px 8px;
    margin-left: 8px;
    font-size: 14px;
    font-weight: 500;
    outline: none;
    box-shadow: none;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
}
.files-container {
    margin-top: 10px;
    margin-bottom: 15px;
}
.files-container .files-list {
    margin: 10px;
    border: solid 1px #444;
    border-radius: 8px;
    text-align: left;
    padding: 10px;
    background-color: #2a2d3a;
    list-style: none;
}
.files-container .files-list li {
    border-left: none;
    padding: 5px 0;
    cursor: pointer;
    color: #E2E2E2;
    transition: color 0.2s;
}
.files-container .files-list li:hover { color: #fff; }
.files-container .files-list li i {
    margin-right: 8px;
    color: #7A7B82;
}
.files-container .files-header {
    border-left: none;
    margin-left: 0;
    font-weight: bold;
    color: #E2E2E2;
    display: block;
    margin-bottom: 8px;
}
</style>

<style>
.col-lg-2 {
    padding: 0 !important;
}
.nav-side-menu {
    position: fixed !important;
    top: 0px;
    height: 100%;
    overflow: hidden;
    color: rgb(255, 255, 255);
    background: linear-gradient(0deg, rgb(20, 25, 36) 51%, rgb(37, 47, 71) 100%);
}
.sidebar-scroll-container {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
}
.nav-side-menu .toggle-btn {
    display: none;
}
.nav-side-menu ul,
.nav-side-menu li {
    list-style: none;
    padding: 0px;
    margin: 0px;
    line-height: 35px;
    cursor: pointer;
}
.nav-side-menu li {
    padding-left: 15px;
}
.nav-side-menu li:hover {
    background-color: rgba(52, 70, 100, 0.336);
    transition: all 1s ease;
}

a:hover {
    text-decoration: none !important;
}

::-webkit-scrollbar {
    width: 12px;
    background-color: rgba(0, 0, 0, 0);
}
::-webkit-scrollbar-thumb {
    border-radius: 5px;
    box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.1);
    background: rgba(162, 162, 162, 0.452);
}
.filename {
    display: block;
    text-align: left;
    opacity: 0.8;
    margin: 3px;
    margin-bottom: 10px;
    padding-left: 10px;
    font-size: 14px;
}
@media only screen and (max-width: 992px) {
    .nav-side-menu {
        position: fixed;
        width: 100%;
        height: auto;
        max-height: 100%;
        z-index: 1002;
    }
}
@media only screen and (min-width: 991px) and (max-width: 1439px) {
    .nav-side-menu {
        max-width: 27% !important;
    }
}
@media only screen and (min-width: 1440px) and (max-width: 2000px) {
    .nav-side-menu {
        max-width: 20% !important;
    }
}
@media only screen and (min-width: 2000px) {
    .nav-side-menu {
        max-width: 15% !important;
    }
}
</style>
