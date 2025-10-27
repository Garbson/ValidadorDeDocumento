import { defineStore } from 'pinia'

export const useTempStore = defineStore('temp', {
  state: () => ({
    layoutFile: null,
    layoutData: null,
    layoutFilename: null
  }),
  actions: {
    setLayout(file, data){
      this.layoutFile = file
      this.layoutData = data || null
    },
    setLayoutFromFilename(filename, data){
      this.layoutFile = null
      this.layoutFilename = filename || null
      this.layoutData = data || null
    },
    clear(){
      this.layoutFile = null
      this.layoutData = null
      this.layoutFilename = null
    }
  }
})
