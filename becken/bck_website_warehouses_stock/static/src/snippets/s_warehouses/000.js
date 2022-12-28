odoo.define('bck_website_warehouses_stock.s_warehouses', function(require) {
  'use strict';

  const publicWidget = require('web.public.widget')

  publicWidget.registry.warehousesStock = publicWidget.Widget.extend({
    selector: '.s_warehouse_stock',
    start: function () {
      let self = this
      const productIdFields = $('.js_product > input[name="product_id"][type="hidden"]')

      if (productIdFields.length === 1) {
        const product_id = productIdFields[0].value
        this._rpc({
          route: `/bck_warehouses_stock/stocks/${product_id}`
        }).then(function(data) {

          self.$('.bck_warehouses_details').html(data)
        })
      }
      console.log('start')
      return this._super.apply(this, arguments)
    }
  })
  return publicWidget.registry.warehousesStock
})

// import publicWidget from 'web.public.widget'

// publicWidget.registry.WarehousesStock = publicWidget.Widget.extend({

//   selector: '.s_warehouse_stock',
//   // xmlDependencies: ['/bck_website_warehouses_stock/static/src/snippets/s_warehouses/000.xml'],
//   // template: 'bck_website_warehouses_stock.warehouses_stock_view',

//   start: function () {
//     let self = this
//     const productIdFields = $('.js_product > input[name="product_id"][type="hidden"]')
//     console.log('Cantidad de productos en este momento...', productIdFields)
//     if (productIdFields.length === 1) {
//       const product_id = productIdFields[0].value
//       this._rpc({
//         route: `/bck_warehouses_stock/stocks/${product_id}`
//       }).then(function(data) {
//         console.log('antes de agregar a las existencias')
//         console.log(data)
//         console.log('bck_warehouses_details')
//         self.$('.bck_warehouses_details').html(data)
//       })
//     }
//     console.log('start')
//     return this._super.apply(this, arguments)
//   }

// })

// export default publicWidget.registry.WarehousesStock