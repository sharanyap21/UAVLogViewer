<template>
    <div>
        <!-- <li  v-if="file==null && !sampleLoaded" >
            <a @click="onLoadSample('sample')" class="section" id="open-sample">Play Sample</a>
        </li> -->
        <li v-if="url">
            <a @click="share" class="section"><i class="fas fa-share-alt"></i> {{ shared ? 'Copied to clipboard!' :
                'Share link'}}</a>
        </li>
        <li v-if="url">
            <a :href="'/uploaded/' + url" class="section" target="_blank"><i class="fas fa-download"></i> Download</a>
        </li>
        <div class="sidebar-bottom-bar">
            <div @click="browse" @dragover.prevent @drop="onDrop" id="drop_zone"
                v-if="file==null && uploadpercentage===-1  && !sampleLoaded">
                <i id="plus-icon" class="fa fa-plus"></i>
                <p class="upload-text">Upload a test file</p>
                <input @change="onChange" id="choosefile" style="opacity: 0;" type="file">
            </div>
            <button
                class="sample-help-btn"
                type="button"
                @click.stop="onLoadSample('sample')"
                title="Try a sample file"
            >
                <img class="help-icon-img" :src="infoCircleSvg" alt="info" />
            </button>
        </div>
        <!--<b-form-checkbox @change="uploadFile()" class="uploadCheckbox" v-if="file!=null && !uploadStarted"> Upload
        </b-form-checkbox>-->
        <VProgress v-bind:complete="transferMessage"
                   v-bind:percent="uploadpercentage"
                   v-if="uploadpercentage > -1">
        </VProgress>
        <VProgress v-bind:complete="state.processStatus"
                   v-bind:percent="state.processPercentage"
                   v-if="state.processPercentage > -1"
        ></VProgress>
    </div>
</template>
<script>
import VProgress from './SideBarFileManagerProgressBar.vue'
import Worker from '../tools/parsers/parser.worker.js'
import { store } from './Globals'
import infoCircleSvg from '../assets/info.circle.svg'

import { MAVLink20Processor as MAVLink } from '../libs/mavlink'

const worker = new Worker()

worker.addEventListener('message', function (event) {
})

export default {
    name: 'Dropzone',
    data: function () {
        return {
            // eslint-disable-next-line no-undef
            mavlinkParser: new MAVLink(),
            uploadpercentage: -1,
            sampleLoaded: false,
            shared: false,
            url: null,
            transferMessage: '',
            state: store,
            file: null,
            uploadStarted: false,
            infoCircleSvg
        }
    },
    created () {
        this.$eventHub.$on('loadType', this.loadType)
        this.$eventHub.$on('trimFile', this.trimFile)
    },
    beforeDestroy () {
        this.$eventHub.$off('open-sample')
    },
    methods: {
        trimFile () {
            worker.postMessage({ action: 'trimFile', time: this.state.timeRange })
        },
        onLoadSample (file) {
            let url
            if (file === 'sample') {
                this.state.file = 'sample'
                url = require('../assets/vtol.tlog').default
                this.state.logType = 'tlog'
            } else {
                url = file
                // Set the file name for display purposes
                const urlParts = url.split('/')
                this.state.file = urlParts[urlParts.length - 1]
            }
            const oReq = new XMLHttpRequest()
            console.log(`loading file from ${url}`)

            // Set the log type based on file extension
            this.state.logType = url.indexOf('.tlog') > 0 ? 'tlog' : 'bin'
            if (url.indexOf('.txt') > 0) {
                this.state.logType = 'dji'
            }

            oReq.open('GET', url, true)
            oReq.responseType = 'arraybuffer'

            // Use arrow function to preserve 'this' context
            oReq.onload = (oEvent) => {
                const arrayBuffer = oReq.response

                this.transferMessage = 'Download Done'
                this.sampleLoaded = true
                worker.postMessage({
                    action: 'parse',
                    file: arrayBuffer,
                    isTlog: (url.indexOf('.tlog') > 0),
                    isDji: (url.indexOf('.txt') > 0)
                })
            }
            oReq.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    this.uploadpercentage = 100 * e.loaded / e.total
                }
            }
            , false)
            oReq.onerror = (error) => {
                alert('unable to fetch remote file, check CORS settings in the target server')
                console.log(error)
            }

            oReq.send()
        },
        onChange (ev) {
            const fileinput = document.getElementById('choosefile')
            this.process(fileinput.files[0])
        },
        onDrop (ev) {
            // Prevent default behavior (Prevent file from being opened)
            ev.preventDefault()
            if (ev.dataTransfer.items) {
                // Use DataTransferItemList interface to access the file(s)
                for (let i = 0; i < ev.dataTransfer.items.length; i++) {
                    // If dropped items aren't files, reject them
                    if (ev.dataTransfer.items[i].kind === 'file') {
                        const file = ev.dataTransfer.items[i].getAsFile()
                        this.process(file)
                    }
                }
            } else {
                // Use DataTransfer interface to access the file(s)
                for (let i = 0; i < ev.dataTransfer.files.length; i++) {
                    console.log('... file[' + i + '].name = ' + ev.dataTransfer.files[i].name)
                    console.log(ev.dataTransfer.files[i])
                }
            }
        },
        loadType: function (type) {
            worker.postMessage({
                action: 'loadType',
                type: type
            })
        },
        process: function (file) {
            this.state.file = file.name
            this.state.processStatus = 'Pre-processing...'
            this.state.processPercentage = 100
            this.file = file
            const reader = new FileReader()
            reader.onload = function (e) {
                const data = reader.result
                worker.postMessage({
                    action: 'parse',
                    file: data,
                    isTlog: (file.name.endsWith('tlog')),
                    isDji: (file.name.endsWith('txt'))
                })
            }
            this.state.logType = file.name.endsWith('tlog') ? 'tlog' : 'bin'
            if (file.name.endsWith('.txt')) {
                this.state.logType = 'dji'
            }
            reader.readAsArrayBuffer(file)
        },
        uploadFile () {
            this.uploadStarted = true
            this.transferMessage = 'Upload Done!'
            this.uploadpercentage = 0
            const formData = new FormData()
            formData.append('file', this.file)

            const request = new XMLHttpRequest()
            request.onload = () => {
                if (request.status >= 200 && request.status < 400) {
                    this.uploadpercentage = 100
                    this.url = request.responseText
                } else {
                    alert('error! ' + request.status)
                    this.uploadpercentage = 100
                    this.transferMessage = 'Error Uploading'
                    console.log(request)
                }
            }
            request.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    this.uploadpercentage = 100 * e.loaded / e.total
                }
            }
            , false)
            request.open('POST', '/upload')
            request.send(formData)
        },
        fixData (message) {
            if (message.name === 'GLOBAL_POSITION_INT') {
                message.lat = message.lat / 10000000
                message.lon = message.lon / 10000000
                // eslint-disable-next-line
                message.relative_alt = message.relative_alt / 1000
            }
            return message
        },
        browse () {
            document.getElementById('choosefile').click()
        },
        share () {
            const el = document.createElement('textarea')
            el.value = window.location.host + '/#/v/' + this.url
            document.body.appendChild(el)
            el.select()
            document.execCommand('copy')
            document.body.removeChild(el)
            this.shared = true
        },
        downloadFileFromURL (url) {
            const a = document.createElement('a')
            document.body.appendChild(a)
            a.style = 'display: none'
            a.href = url
            a.download = this.state.file + '-trimmed.' + this.state.logType
            a.click()
            document.body.removeChild(a)
            window.URL.revokeObjectURL(url)
        }
    },
    mounted () {
        window.addEventListener('message', (event) => {
            if (event.data.type === 'arrayBuffer') {
                worker.postMessage({
                    action: 'parse',
                    file: event.data.data,
                    isTlog: false,
                    isDji: false
                })
            }
        })
        worker.onmessage = (event) => {
            if (event.data.percentage) {
                this.state.processPercentage = event.data.percentage
            } else if (event.data.availableMessages) {
                this.$eventHub.$emit('messageTypes', event.data.availableMessages)
            } else if (event.data.metadata) {
                this.state.metadata = event.data.metadata
            } else if (event.data.messages) {
                this.state.messages = event.data.messages
                this.$eventHub.$emit('messages')
            } else if (event.data.messagesDoneLoading) {
                this.$eventHub.$emit('messagesDoneLoading')
            } else if (event.data.messageType) {
                this.state.messages[event.data.messageType] = event.data.messageList
                this.$eventHub.$emit('messages')
            } else if (event.data.files) {
                this.state.files = event.data.files
                this.$eventHub.$emit('messages')
            } else if (event.data.url) {
                this.downloadFileFromURL(event.data.url)
            }
        }
        const url = document.location.search.split('?file=')[1]
        if (url) {
            this.onLoadSample(decodeURIComponent(url))
        }
    },
    components: {
        VProgress
    }
}
</script>
<style scoped>
.sidebar-bottom-bar {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 13px;
    width: 100%;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    background: none;
    z-index: 10;
    min-width: 260px;
}
#drop_zone {
    background-color: #32343F;
    color: #7A7B82;
    font-size: 14px;
    font-family: 'SF Pro Text', 'San Francisco', 'Segoe UI', 'Arial', 'sans-serif';
    border-radius: 15px;
    padding: 3px 5px;
    height: 40px;
    width: 225px;
    cursor: pointer;
    box-sizing: border-box;
    white-space: nowrap;
    display: inline-block;
    vertical-align: middle;
    position: static;
}
#plus-icon,
.upload-text {
    display: inline-block;
    vertical-align: middle;
}
#plus-icon {
    font-size: 1.2em;
    margin-right: 15px;
}
.upload-text {
    margin: 0;
    display: inline-block;
    vertical-align: middle;
}
.sample-help-btn {
    background: none;
    border: none;
    color: #7A7B82;
    font-size: 1.2em;
    margin-left: 8px;
    cursor: pointer;
    padding: 0;
    border-radius: 50%;
    transition: background 0.2s;
    display: inline-block;
    vertical-align: middle;
    height: 40px;
    width: 40px;
    min-width: 40px;
    min-height: 40px;
    line-height: 40px;
    text-align: center;
    position: relative;
}
.sample-help-btn:hover {
    background: #23253a;
}
.sample-help-btn img {
    width: 20px;
    height: 20px;
    display: inline-block;
    vertical-align: middle;
    pointer-events: none;
}
</style>
