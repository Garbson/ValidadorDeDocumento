import { defineStore } from 'pinia'

export const useTempStore = defineStore('temp', {
  state: () => ({
    layoutFile: null,
    layoutData: null
  }),
  actions: {
    setLayout(file, data){
      this.layoutFile = file
      this.layoutData = data || null
    },
    clear(){
      this.layoutFile = null
      this.layoutData = null
    }
  }
})
