async function parseBody(body) {
  const container = []

  Array.from(body.querySelectorAll('tr')).forEach(node => {
    const result = Array.from(node.querySelectorAll('td')).map(column => {
      return column.textContent.trim().normalize('NFC')
    })
    container.push(result)
  })

  return container
}

async function parseHeader(head) {
  return Array.from(head.querySelectorAll('th:not([hidden])')).map(node => {
    return {
      column: node.getAttribute('data-field'),
      name: node.textContent.trim() || null
    }
  })
}

async function parseTable() {
  let columns = []
  let data = []
  const wrapper = document.querySelector('.nba-stat-table__overflow')

  if (wrapper) {
    const table = wrapper.querySelector('table')

    if (table) {
      // parseRows(table)
      const tHead = table.querySelector('thead')
      const tBody = table.querySelector('tbody')
    
      columns = await parseHeader(tHead)
      data = await parseBody(tBody)
      
      return {
        columns,
        data
      }
    }
  }
}

parseTable()
